"""
License activation, status, branding, and logo upload.

Mirrors the canteen blueprint's wiring: routes are defined inside
register_license_routes() so require_role can be injected from index.py without a
circular import. Activation is owner-only; branding is public because the club's
name and logo appear on the login screen and customer portal before anyone signs in.
"""
import json
import os
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import urllib.request
import uuid as _uuid

from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from models import db
from license_util import (
    verify_token, store_license, license_status, active_license, LicenseError,
    device_fingerprint, clear_license, store_branch_license, _brand_logo_url, is_licensed)

license_bp = Blueprint("license", __name__, url_prefix="/api")

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp", "svg"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Where installs fetch their token online (your license authority). The offline
# paste path never needs this.
LICENSE_SERVER_URL = os.environ.get("LICENSE_SERVER_URL", "").rstrip("/")


def register_license_routes(app, require_role):

    @license_bp.route("/branding", methods=["GET"])
    def branding():
        """Public: the club's name + logo, for pre-login and customer surfaces.
        Falls back to nulls (the UI shows the product default) when unactivated."""
        lic = active_license()
        return jsonify({
            "clubName": lic.club_name if lic else None,
            "logoUrl": (lic.logo_url or _brand_logo_url(lic.club_uid)) if lic else None,  # local first, licence-server fallback
        })

    @license_bp.route("/license", methods=["GET"])
    def status():
        return jsonify(license_status())

    @license_bp.route("/license/device-id", methods=["GET"])
    def device_id():
        """This machine's fingerprint, for the owner to send in to be licensed.
        Computed on the server (a browser can't read hardware ids)."""
        return jsonify({"fingerprint": device_fingerprint()})

    @license_bp.route("/license/activate", methods=["POST"])
    def activate():
        """Offline path: the owner uploads the license file issued by the vendor."""
        if "token" not in request.files or request.files["token"].filename == "":
            return jsonify({"error": "No file provided."}), 400
        raw = request.files["token"].read(64 * 1024)   # licenses are ~300 bytes; cap the read
        if not raw:
            return jsonify({"error": "That file is empty."}), 400
        try:
            token = raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            return jsonify({"error": "That doesn't look like a license file."}), 400
        # The signature — not the extension — is what makes a token valid, so we
        # just try to verify whatever's inside.
        try:
            store_license(token)
        except LicenseError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(license_status())

    @license_bp.route("/license/deactivate", methods=["POST"])
    def deactivate():
        require_role("owner")                       # destructive: only the owner
        clear_license()                             # drops the stored license → gate returns
        return jsonify({"ok": True})

    @license_bp.route("/license/branch/activate", methods=["POST"])
    def activate_branch():
        """Apply a branch's license token (issued by the license server). Part of
        the activation gate — reachable pre-login; the SIGNED token is the auth,
        so no staff session is required. Accepts JSON {token, name?} or a file."""
        token, name = "", None
        if request.is_json:
            body = request.get_json(silent=True) or {}
            token = (body.get("token") or "").strip()
            name = (body.get("name") or None)
        elif "token" in request.files:
            raw = request.files["token"].read(64 * 1024)
            try:
                token = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                return jsonify({"error": "That doesn't look like a license file."}), 400
        if not token:
            return jsonify({"error": "No branch token provided."}), 400
        try:
            bl = store_branch_license(token, name=name)
        except LicenseError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"ok": True, "branch": {"uid": bl.branch_uid, "name": bl.name,
                                               "features": __import__("json").loads(bl.entitlements or "[]")}})

    @license_bp.route("/license/fetch", methods=["POST"])
    def fetch():
        """Online path: pull the token from the vendor's license server by uid+code."""
        if not LICENSE_SERVER_URL:
            return jsonify({"error": "Online activation isn't configured. "
                                     "Paste the license token instead."}), 400
        data = request.json or {}
        uid, code = data.get("uid", "").strip(), data.get("code", "").strip()
        if not uid:
            return jsonify({"error": "Club ID is required."}), 400
        url = f"{LICENSE_SERVER_URL}/license/{uid}?{urlencode({'code': code})}"
        try:
            with urlopen(url, timeout=10) as r:
                token = (json.loads(r.read().decode()) or {}).get("token", "")
        except HTTPError:
            return jsonify({"error": "No license found for that ID/code."}), 404
        except (URLError, ValueError):
            return jsonify({"error": "Couldn't reach the license server. "
                                     "Check the connection or paste the token instead."}), 502
        try:
            store_license(token)
        except LicenseError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(license_status())

    @license_bp.route("/license/logo", methods=["POST"])
    def upload_logo():
        require_role("owner")
        if not is_licensed():
            return jsonify({"error": "Activate a license before uploading a logo."}), 400
        lic = active_license()   # provisioned from the branch licences; non-None once licensed
        if "logo" not in request.files or request.files["logo"].filename == "":
            return jsonify({"error": "No file provided."}), 400
        file = request.files["logo"]
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXT:
            return jsonify({"error": "Unsupported image format."}), 400
        file.seek(0, os.SEEK_END)
        if file.tell() > 4 * 1024 * 1024:
            return jsonify({"error": "Logo must be under 4 MB."}), 400
        file.seek(0)
        filename = secure_filename(f"logo_{lic.club_uid}_{int(datetime.now().timestamp())}.{ext}")
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        # Stored WITHOUT the /api prefix: the frontend prepends API_URL (= "/api")
        # when it renders the logo (BillingReceipt, ManageLicensePage.resolveLogoSrc).
        lic.logo_url = f"/license/media/{filename}"
        db.session.commit()
        # Back the logo up on the licence server (keyed by club uuid) so it
        # survives a reinstall / new device. Best-effort: the local copy above
        # is what's actually served, so an offline push failing is harmless.
        if LICENSE_SERVER_URL and lic.club_uid and lic.token:
            try:
                with open(os.path.join(UPLOAD_FOLDER, filename), "rb") as _fh:
                    raw = _fh.read()
                boundary = "----baize" + _uuid.uuid4().hex
                body = (
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"token\"\r\n\r\n{lic.token}\r\n".encode()
                    + f"--{boundary}\r\nContent-Disposition: form-data; name=\"logo\"; filename=\"{filename}\"\r\nContent-Type: image/{ext}\r\n\r\n".encode()
                    + raw + f"\r\n--{boundary}--\r\n".encode()
                )
                req = urllib.request.Request(
                    f"{LICENSE_SERVER_URL}/license/{lic.club_uid}/logo", data=body,
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
                urllib.request.urlopen(req, timeout=6)
            except Exception:
                pass
        return jsonify({"logoUrl": lic.logo_url})

    @license_bp.route("/branding/logo", methods=["GET"])
    def serve_current_logo():
        """Stable public URL for the club's CURRENT logo, so other apps (the
        customer app) can reference it by the club's public_url without knowing
        the timestamped filename. Falls back to the newest uploaded file."""
        lic = active_license()
        url = (getattr(lic, "logo_url", None) if lic else None) or ""
        if url.startswith("/license/media/"):
            fn = url.rsplit("/", 1)[-1]
            if os.path.exists(os.path.join(UPLOAD_FOLDER, fn)):
                return send_from_directory(UPLOAD_FOLDER, fn)
        import glob
        files = sorted(glob.glob(os.path.join(UPLOAD_FOLDER, "logo_*")),
                       key=os.path.getmtime, reverse=True)
        if files:
            return send_from_directory(UPLOAD_FOLDER, os.path.basename(files[0]))
        return ("", 404)

    @license_bp.route("/license/media/<path:filename>", methods=["GET"])
    def serve_logo(filename):
        """Public: the logo is shown before login and on the customer portal."""
        return send_from_directory(UPLOAD_FOLDER, filename)

    app.register_blueprint(license_bp)