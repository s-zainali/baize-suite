"""
Seed ~1 year of realistic demo data for an enterprise, multi-branch club.

WHY A SCRIPT (not SQL): raw INSERTs that set explicit primary keys leave
PostgreSQL's id sequences behind, so the app's next insert collides
(duplicate key ... play_session_pkey). This runs through the ORM, so every id
is assigned by the sequence — it can never cause that error.

RUN (from backend/, with your venv active and DATABASE_URL set):
    python api/seed_demo.py            # create structure if missing + a year of history
    python api/seed_demo.py --wipe     # clear operational history first, then reseed

It generates settled ActivityLog bills + paid CanteenOrders across the past
year (the tables reconciliation & analytics read), for 3 branches of 13
stations each, with realistic opening hours, weekend peaks, payment mix, khata,
and canteen tabs. Licenses, customers and staff logins are left untouched.
"""
import json
import random
import sys
from datetime import datetime, timedelta, time

from index import app, seed_table_types          # importing index builds the Flask app + db
from models import (db, Branch, Lounge, PoolTable, GlobalRate, TableType, User,
                    CanteenProduct, CanteenOrder, CanteenOrderItem, ActivityLog)

# ── knobs ────────────────────────────────────────────────────────────────────
DAYS = 365
AVG_SESSIONS_PER_STATION_PER_DAY = 6.0     # weekday baseline; weekends scale up
SEED = 42
random.seed(SEED)

OPEN_HOUR, CLOSE_HOUR = 12, 26              # 12:00 → 02:00 next day (26 = 2 AM)
PAY_MIX = (['cash'] * 55 + ['easypaisa'] * 20 + ['jazzcash'] * 15 + ['khata'] * 10)
CANTEEN_ATTACH = 0.35                       # share of table tabs that also order canteen
WALKIN_CANTEEN_PER_DAY = (2, 8)             # standalone counter sales per branch per day

# hourly rate (Rs) per type: (weekday, weekend)
RATES = {
    'snooker': (400, 500), 'pool': (300, 400),
    'privateSnooker': (700, 900), 'privatePool': (600, 800),
    'ps5': (500, 600), 'ps4': (400, 500),
    'xboxx': (500, 600), 'xbox1': (400, 500),
    'pc': (350, 450), 'foosball': (250, 350),
}

# 3 branches; each a list of lounges → station types (≥12 stations each)
BRANCHES = [
    {
        'uid': 'br_690bb8f0a71f', 'name': 'Z Snooker - Branch 1',
        'is_default': True,
        'lounges': {
            'Main Hall':  ['snooker'] * 4 + ['pool'] * 3,
            'VIP Suite':  ['privateSnooker'] * 2 + ['privatePool'] * 1,
            'Arcade':     ['ps5', 'ps4','xbox1','xboxx', 'foosball'],
        },
    },
    {
        'uid': 'br_6f631bd0f9cc', 'name': 'Z Snooker - Branch 2',
        'is_default': False,
        'lounges': {
            'Gaming Zone': ['pc', 'pc', 'pc', 'pc', 'pc'],
            'Cue Room':    ['pool'] * 4,
            'Foosball Bay':['foosball'] * 2,
        },
    },
]

STAFF = ['ahmed', 'bilal', 'sana', 'usman', 'hina']   # served_by pool
GUESTS = ['Ali Raza', 'Zain Ali', 'Hamza Sheikh', 'Fatima N.', 'Omar F.', 'Bilal K.',
          'Sara M.', 'Danish', 'Rehan', 'Ayesha', 'Talha', 'Mehwish', 'Kamran', 'Noor',
          'Faisal', 'Junaid', 'Areeba', 'Saad', 'Hassan', 'Maria', 'Waleed', 'Iqra']
CANTEEN_MENU = [
    ('Chai', 'hot', 80, '☕'), ('Coffee', 'hot', 150, '☕'), ('Green Tea', 'hot', 100, '🍵'),
    ('Cold Drink', 'cold', 120, '🥤'), ('Water', 'cold', 60, '💧'), ('Red Bull', 'cold', 400, '🧃'),
    ('Fresh Juice', 'cold', 250, '🧃'), ('Lassi', 'cold', 180, '🥛'),
    ('Chips', 'snacks', 100, '🍟'), ('Nimko', 'snacks', 90, '🥜'), ('Samosa', 'snacks', 60, '🥟'),
    ('Pakora Plate', 'snacks', 200, '🧆'), ('Peanuts', 'snacks', 80, '🥜'),
    ('Club Sandwich', 'meals', 450, '🥪'), ('Zinger Burger', 'meals', 550, '🍔'),
    ('Chicken Roll', 'meals', 350, '🌯'), ('Chicken Biryani', 'meals', 400, '🍛'),
    ('Loaded Fries', 'meals', 350, '🍟'),
    ('Ice Cream', 'sweets', 200, '🍦'), ('Chocolate Brownie', 'sweets', 300, '🍫'),
    ('Gulab Jamun', 'sweets', 150, '🍮'),
    ('Cigarette (single)', 'smokes', 40, '🚬'), ('Gold Leaf Pack', 'smokes', 420, '🚬'),
    ('Lighter', 'smokes', 100, '🔥'),
]

# On-credit (khata) realism: only a few regulars run tabs, and each guest's
# OUTSTANDING credit is capped to a few thousand PKR — past that they pay.
KHATA_CAP = 4000
KHATA_REGULARS = GUESTS[:6]


def _dt(day, hour_float):
    """A naive datetime `day` at `hour_float` (hours can exceed 24 → next day)."""
    base = datetime.combine(day, time(0, 0))
    return base + timedelta(hours=hour_float)


def wipe_history():
    print("• wiping operational history…")
    for Model in (CanteenOrderItem, CanteenOrder, ActivityLog):
        db.session.query(Model).delete()
    # also clear the physical layout so re-seeding doesn't duplicate stations
    from models import Queue, Booking, SessionSegment, SessionPlayer, PlaySession
    for Model in (Queue, Booking, SessionSegment, SessionPlayer, PlaySession,
                  PoolTable, Lounge, CanteenProduct):
        db.session.query(Model).delete()
    # branches only if they are demo branches
    db.session.query(Branch).filter(Branch.uid.in_([b['uid'] for b in BRANCHES])).delete(synchronize_session=False)
    db.session.commit()


def ensure_structure():
    """Create branches, lounges, stations, rates, products, staff if missing."""
    seed_table_types()  # station-type registry (renderers) — safe/idempotent
    known_types = {t.key for t in TableType.query.all()}

    # global rates
    for key, (wd, we) in RATES.items():
        if key in known_types and not GlobalRate.query.filter_by(table_type=key).first():
            db.session.add(GlobalRate(table_type=key, weekday_rate=wd, weekend_rate=we))

    # staff (owner may already exist; add a few receptionists/managers, no clash)
    for i, u in enumerate(STAFF):
        if not User.query.filter_by(username=u).first():
            usr = User(username=u, role='manager' if i == 0 else 'receptionist',
                       capabilities='floor,canteen')
            usr.set_password('demo1234')
            db.session.add(usr)
    db.session.commit()

    branches = []
    for spec in BRANCHES:
        b = Branch.query.filter_by(uid=spec['uid']).first()
        if not b:
            b = Branch(uid=spec['uid'], name=spec['name'], address=spec['address'],
                       status='active', is_default=spec['is_default'],
                       sort_order=len(branches))
            db.session.add(b)
            db.session.flush()
        stations = []
        lo_sort = 0
        for lo_name, types in spec['lounges'].items():
            luid = f"{spec['uid']}_lo_{lo_sort}"
            lo = Lounge.query.filter_by(uid=luid).first()
            if not lo:
                lo = Lounge(uid=luid, name=lo_name, status='active',
                            sort_order=lo_sort, branch_id=b.id)
                db.session.add(lo)
                db.session.flush()
            for j, ttype in enumerate(types):
                tuid = f"{luid}_t{j}"
                if not PoolTable.query.filter_by(uid=tuid).first():
                    db.session.add(PoolTable(
                        uid=tuid, table_id=str(j + 1), table_type=ttype,
                        is_active=False, booking_name='', start_time=None,
                        sort_order=j, lounge_uid=luid, status='active', branch_id=b.id))
                stations.append({'uid': tuid, 'id': str(j + 1), 'type': ttype,
                                 'lounge': lo_name})
            lo_sort += 1

        # per-branch canteen menu
        for k, (nm, cat, price, emoji) in enumerate(CANTEEN_MENU):
            if not CanteenProduct.query.filter_by(name=nm, branch_id=b.id).first():
                db.session.add(CanteenProduct(name=nm, category=cat, price=price, emoji=emoji,
                                              stock=999, is_active=True, sort_order=k, branch_id=b.id))
        branches.append({'id': b.id, 'spec': spec, 'stations': stations})
    db.session.commit()
    return branches


def gen_year(branches):
    order_seq = (CanteenOrder.query.count() or 0)
    receipt_seq = 100000
    today = datetime.now().date()
    start = today - timedelta(days=DAYS)
    totals = {'bills': 0, 'canteen': 0, 'revenue': 0}
    khata_balance = {}          # guest -> outstanding credit (kept ≤ KHATA_CAP)

    for d in range(DAYS):
        day = start + timedelta(days=d)
        weekend = day.weekday() >= 5                    # Sat/Sun peak
        day_logs = []                                   # ActivityLog dicts (bulk insert)
        day_orders = []                                 # (CanteenOrder, [item dicts])

        for br in branches:
            menu = CanteenProduct.query.filter_by(branch_id=br['id']).all()
            for st in br['stations']:
                rate_wd, rate_we = RATES.get(st['type'], (300, 400))
                rate = rate_we if weekend else rate_wd
                n = max(0, int(random.gauss(
                    AVG_SESSIONS_PER_STATION_PER_DAY * (1.5 if weekend else 1.0), 1.6)))
                for _ in range(n):
                    # start hour weighted toward the evening
                    h = random.choices(
                        population=[13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25],
                        weights=[3, 4, 6, 9, 12, 14, 14, 12, 9, 6, 3])[0] + random.random()
                    dur = random.choice([30, 45, 60, 60, 90, 90, 120, 150, 180])
                    started = _dt(day, h)
                    ended = started + timedelta(minutes=dur)
                    total = round(rate * dur / 60)
                    pay = random.choice(PAY_MIX)
                    guest = random.choice(GUESTS)
                    staff = random.choice(STAFF)
                    receipt_seq += 1
                    bill_group = None

                    # Build the canteen tab first (if any) so the khata cap can
                    # weigh the WHOLE tab, not just the table time.
                    canteen_total = 0
                    item_dicts = None
                    if random.random() < CANTEEN_ATTACH and menu:
                        bill_group = f"bg_{br['id']}_{receipt_seq}"
                        items = random.sample(menu, k=random.randint(1, min(3, len(menu))))
                        item_dicts, sub = [], 0
                        for p in items:
                            qty = random.randint(1, 3)
                            line = p.price * qty
                            sub += line
                            item_dicts.append({'product_id': p.id, 'name': p.name,
                                               'unit_price': p.price, 'qty': qty, 'line_total': line})
                        canteen_total = sub

                    # Khata only for regulars, and only while their outstanding
                    # stays within a few thousand — otherwise they settle up.
                    tab = total + canteen_total
                    is_khata = (pay == 'khata' and guest in KHATA_REGULARS
                                and khata_balance.get(guest, 0) + tab <= KHATA_CAP)
                    if is_khata:
                        khata_balance[guest] = khata_balance.get(guest, 0) + tab
                    elif pay == 'khata':
                        pay = random.choice(['cash', 'easypaisa', 'jazzcash'])   # paid instead of tabbing

                    if item_dicts is not None:
                        order_seq += 1
                        co = CanteenOrder(
                            branch_id=br['id'], order_no=f"C-{order_seq:06d}",
                            target_label=f"{st['type']} #{st['id']}", table_uid=st['uid'],
                            session_id=None, subtotal=canteen_total, discount_percent=0, discount_amount=0,
                            total=canteen_total, payment_method='' if is_khata else pay,
                            payment_status='pending' if is_khata else 'paid',
                            settled_at=None if is_khata else ended,
                            khata_name=guest if is_khata else None,
                            closed_at=ended, closed_by=staff, bill_group=bill_group,
                            status='paid', served_by=staff, created_at=started)
                        day_orders.append((co, item_dicts))
                        totals['canteen'] += 1

                    day_logs.append({
                        'branch_id': br['id'], 'receipt_id': receipt_seq,
                        'date_string': started.strftime('%a, %d %b %Y %I:%M %p'),
                        'lounge': st['lounge'], 'table_type': st['type'], 'table_id': st['id'],
                        'player': guest, 'elapsed': f"{dur // 60}h {dur % 60}m",
                        'billable_mins': dur, 'rate': rate, 'total_cost': total,
                        'session_id': None,
                        'segments_json': json.dumps([{'tableType': st['type'], 'tableNumber': st['id'],
                                                       'loungeName': st['lounge'], 'rate': rate,
                                                       'mins': dur}]),
                        'canteen_json': None, 'play_total': total,
                        'canteen_total': canteen_total or None, 'split_count': None,
                        'created_at': started, 'served_by': staff,
                        'payment_status': 'pending' if is_khata else 'paid',
                        'payment_method': '' if is_khata else pay,
                        'settled_at': None if is_khata else ended,
                        'khata_name': guest if is_khata else None, 'customer_id': None,
                        'closed_at': ended, 'closed_by': staff, 'bill_group': bill_group,
                    })
                    totals['bills'] += 1
                    totals['revenue'] += total + canteen_total

            # standalone walk-in canteen sales
            if menu:
                for _ in range(random.randint(*WALKIN_CANTEEN_PER_DAY)):
                    h = random.uniform(OPEN_HOUR, CLOSE_HOUR)
                    when = _dt(day, h)
                    staff = random.choice(STAFF)
                    items = random.sample(menu, k=random.randint(1, min(3, len(menu))))
                    item_dicts, sub = [], 0
                    for p in items:
                        qty = random.randint(1, 4)
                        line = p.price * qty
                        sub += line
                        item_dicts.append({'product_id': p.id, 'name': p.name,
                                           'unit_price': p.price, 'qty': qty, 'line_total': line})
                    pay = random.choice(['cash', 'cash', 'easypaisa', 'jazzcash'])
                    order_seq += 1
                    co = CanteenOrder(
                        branch_id=br['id'], order_no=f"C-{order_seq:06d}", target_label='Walk-in',
                        table_uid=None, session_id=None, subtotal=sub, discount_percent=0,
                        discount_amount=0, total=sub, payment_method=pay, payment_status='paid',
                        settled_at=when, closed_at=when, closed_by=staff, bill_group=None,
                        status='paid', served_by=staff, created_at=when)
                    day_orders.append((co, item_dicts))
                    totals['canteen'] += 1
                    totals['revenue'] += sub

        # persist the day: bills via fast bulk insert; orders need ids for their items
        if day_logs:
            db.session.bulk_insert_mappings(ActivityLog, day_logs)
        if day_orders:
            db.session.add_all([co for co, _ in day_orders])
            db.session.flush()                          # populates order ids
            item_rows = []
            for co, items in day_orders:
                for it in items:
                    it['order_id'] = co.id
                    item_rows.append(it)
            db.session.bulk_insert_mappings(CanteenOrderItem, item_rows)
        db.session.commit()
        if d % 30 == 0:
            print(f"  … {day.isoformat()}  bills={totals['bills']:,}  canteen={totals['canteen']:,}")

    return totals


def main():
    with app.app_context():
        if '--wipe' in sys.argv:
            wipe_history()
        print("• ensuring branches / stations / rates / menu / staff…")
        branches = ensure_structure()
        print(f"• seeding {DAYS} days across {len(branches)} branches…")
        totals = gen_year(branches)
        print("\n✓ done")
        print(f"  branches      : {len(branches)}")
        print(f"  table bills   : {totals['bills']:,}")
        print(f"  canteen sales : {totals['canteen']:,}")
        print(f"  gross revenue : Rs {totals['revenue']:,}")
        print("  staff logins  : " + ", ".join(f"{u}/demo1234" for u in STAFF))


if __name__ == '__main__':
    main()