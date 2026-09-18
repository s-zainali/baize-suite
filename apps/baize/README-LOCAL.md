# Baize — local install (compiled, license-enforced)

## Layout (put the whole repo + these files in /opt/baize on the club's box)
  Dockerfile.local  docker-compose.local.yml  baize.env  public.pem  start.sh  baize.desktop
  backend/  frontend/            <- your source (used only to BUILD; not shipped inside the image)

## 1. One-time prep
- Set  build: { sourcemap: false }  in frontend/vite.config.js  (no source maps).
- Put your license server's PUBLIC key into  public.pem.
- Edit baize.env if needed (DB creds/port are fine as-is).

## 2. Build  (Linux / WSL, Docker installed)
    cd /opt/baize
    VITE_LICENSE_SERVER_URL=https://license.baize.pk docker compose -f docker-compose.local.yml build
  (First build is slow — Nuitka compiles the backend to a native binary. If it
   fails with `ModuleNotFoundError: X`, add `--include-package=X` in Dockerfile.local and rebuild.)

## 3. Run
    ./start.sh
  Brings up Postgres + the app, waits, then opens the fullscreen kiosk window.
  `restart: unless-stopped` means it comes back automatically after a reboot.

## 4. Activate
  The app opens on the activation gate (enforcement is baked in — every /api route
  is 403 until licensed). Sign in as owner → activate with a token you issue from
  the license-server admin (use the device ID shown on the gate for a device-locked
  token, or issue unbound). Revoke from the admin and every endpoint 403s within one
  heartbeat interval.

## Shortcut
  Copy baize.desktop to ~/.local/share/applications/ (or ~/Desktop) and drop a
  baize.png icon in /opt/baize. Double-click = start.sh = app in kiosk mode.
  For auto-start on boot: copy baize.desktop into ~/.config/autostart/.