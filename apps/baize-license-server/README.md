# Baize licensing server

Vendor-side licensing: clubs self-register, the vendor administers them through a
Vue admin portal, and Ed25519-signed license tokens are minted per club. The
Baize app fetches a club's token to activate an install.

    Club 1──* Device      Club 1──* License      AdminEvent (audit)

## Setup

    # 1. signing key (once — the app holds the matching PUBLIC key)
    cd backend && python -c "import signing; print(signing.keygen())"

    # 2. config
    cp backend/.env.example backend/.env    # set ADMIN_TOKEN, secrets, DATABASE_URL

    # 3. database
    docker compose up db                    # Postgres on :5433

    # 4. backend
    pip install -r backend/requirements.txt
    cd backend && flask --app app run -p 8090     # or: gunicorn app:app

    # 5. admin portal (rebuild after any frontend change — the shipped dist/ is stale)
    cd frontend && npm install && npm run build     # emits ../dist, served at /admin

Open **/admin**, sign in with the `ADMIN_TOKEN` (exchanged for a short-lived
session JWT), and you land on the dashboard.

## Admin features
- **Dashboard** — live stats (venues, active/expiring/expired/revoked licenses,
  devices), venue search, and license minting (device-locked or unbound).
- **Venue detail** — profile edit, suspend/reactivate, device un-enrol, and full
  license history with per-license **revoke / restore / renew / copy token /
  copy activation code / download .key**.
- **Licenses** — every token across all venues, filterable by status/search, paginated.
- **Audit** — a log of every vendor action.

## API surface
Club: `POST /api/register`, `/api/login`, `GET /api/me`, `POST /api/devices`.
Admin (Bearer session or `X-Admin-Token`): `POST /api/admin/login`,
`GET /api/admin/{whoami,stats,clubs,clubs/<uuid>,licenses,events}`,
`PATCH /api/admin/clubs/<uuid>`, `POST /api/admin/{issue,devices}`,
`DELETE /api/admin/devices/<id>`,
`POST /api/admin/licenses/<id>/{revoke,unrevoke,renew}`.
App activation: `GET /license/<uuid>?code=<code>` (only active, non-revoked,
non-expired, non-suspended).

## Notes
- Timestamps are stored naive-UTC and serialized as explicit UTC (`…+00:00`).
- Schema is created via `db.create_all()` (adds the new `admin_event` table on
  boot). Adopt **Flask-Migrate** before you start *altering* existing columns.
- Never commit `backend/.env` or the `.private_key.pem`.