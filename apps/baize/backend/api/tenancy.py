"""
Phase 1 — multi-tenant foundation for the CLOUD deployment.

One shared Postgres holds every club's data; isolation is enforced by the
DATABASE (Row-Level Security), not by remembering a WHERE clause. Each request
pins its transaction to the club from the SIGNED licence token; RLS then filters
every read and a column default stamps every insert with that club. A missing
filter in application code therefore cannot leak another club's rows.

Entirely gated by DEPLOY_MODE:
  • local   → inert. Single-club install, no RLS, behaves exactly as before.
  • hybrid  → local install that also syncs to the cloud (cloud DB is tenant-guarded).
  • cloud   → the shared multi-tenant deployment; RLS active.
"""
import os
from sqlalchemy import text

DEPLOY_MODE = os.environ.get('DEPLOY_MODE', 'local').lower()   # local | hybrid | cloud
IS_CLOUD = DEPLOY_MODE == 'cloud'      # multi-tenant + RLS (the shared deployment)
IS_HYBRID = DEPLOY_MODE == 'hybrid'    # local install that also pushes to the cloud

# Every table that holds per-club data. RLS + the club_uid default apply to each.
TENANT_TABLES = [
    'branch', 'queue', 'lounge', 'pool_table', 'play_session', 'session_player',
    'session_segment', 'customer', 'password_reset_code', 'global_rate', 'table_type',
    'booking', 'activity_log', 'canteen_product', 'canteen_order', 'settings',
    'canteen_order_item', 'payment_intent', 'license', 'branch_license', 'user',
]


def resolve_tenant():
    """The club_uid (tenant) for THIS request — from the signature-verified
    licence token's `sub`. Cloud only; None otherwise. Never trusts a request
    body for the tenant."""
    if not IS_CLOUD:
        return None
    # 1) A signed licence/branch token in Authorization (a sync push, or any
    #    token-authed cloud call). This is how the cloud learns WHICH club a
    #    local install's push belongs to. A staff JWT here isn't a licence token,
    #    so it fails verification and falls through — it never resolves falsely.
    try:
        from flask import request, has_request_context
        if has_request_context():
            auth = request.headers.get('Authorization', '')
            if auth.startswith('Bearer '):
                from license_util import _verified_token
                claims = _verified_token(auth[7:])
                if claims and claims.get('sub'):
                    return claims['sub']
    except Exception:
        pass
    # 2) A cloud owner-session JWT carrying club_uid (the owner browsing the
    #    cloud app). A staff JWT isn't a licence token, so path 1 skipped it.
    try:
        from flask import has_request_context
        if has_request_context():
            from flask_jwt_extended import verify_jwt_in_request, get_jwt
            verify_jwt_in_request(optional=True)
            cu = (get_jwt() or {}).get('club_uid')
            if cu:
                return cu
    except Exception:
        pass
    return None   # no tenant resolvable → RLS fail-closed (sees nothing)


def pin_tenant(db, uid):
    """Pin the current transaction to `uid` so RLS filters and the column default
    stamps rows. Empty when unknown → the RLS policy matches nothing (fail-closed:
    an unauthenticated/again-tenant request sees zero rows rather than everything).
    Transaction-scoped via SET LOCAL."""
    db.session.execute(text("SET LOCAL app.club_uid = :u"), {"u": uid or ''})


def enable_rls(db):
    """Idempotently turn on + FORCE row-level security and install the tenant
    isolation policy on every tenant table. Run once at cloud startup. FORCE
    makes even the table owner subject to the policy (so the app's DB user can't
    accidentally bypass it)."""
    for tbl in TENANT_TABLES:
        db.session.execute(text(f'ALTER TABLE IF EXISTS "{tbl}" ENABLE ROW LEVEL SECURITY'))
        db.session.execute(text(f'ALTER TABLE IF EXISTS "{tbl}" FORCE ROW LEVEL SECURITY'))
        db.session.execute(text(
            "DO $$ BEGIN "
            f"IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='{tbl}' AND policyname='tenant_isolation') THEN "
            f"EXECUTE 'CREATE POLICY tenant_isolation ON \"{tbl}\" "
            "USING (club_uid IS NOT DISTINCT FROM current_setting(''app.club_uid'', true)) "
            "WITH CHECK (club_uid IS NOT DISTINCT FROM current_setting(''app.club_uid'', true))'; "
            "END IF; END $$;"
        ))
    db.session.commit()


def install_tenancy(app, db):
    """Wire tenant-pinning into the request lifecycle. No-op unless cloud/hybrid.
    Registered FIRST so the tenant is pinned before any other before_request
    (incl. the licence gate) runs a query."""
    if not IS_CLOUD:
        return

    @app.before_request
    def _pin_tenant_for_request():   # noqa: A003
        try:
            pin_tenant(db, resolve_tenant())
        except Exception:
            pass   # DB not ready / no request DB — queries will simply see nothing