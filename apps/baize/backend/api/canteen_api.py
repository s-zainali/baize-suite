"""Canteen till — part of the STAFF surface.

Every route here sits behind require_role(), so it lives on the staff side of
the staff/customer split. Nothing in the customer blueprint touches it.

The one rule worth stating plainly: the client never decides what anything
costs. It sends product ids and quantities; prices, discounts, totals and stock
are all resolved here. A till that trusts the browser is a till that can be
talked into charging zero.
"""

import os
from datetime import datetime


from flask import Blueprint, jsonify, request, send_from_directory


from models import db, CanteenProduct, CanteenOrder, CanteenOrderItem, PoolTable

canteen_bp = Blueprint('canteen', __name__, url_prefix='/api/canteen')

# imgUrl points at files in frontend/public, so they're served from the site
# root. The emoji stays as a fallback for anywhere an image can't be shown.
CATEGORIES = [
    {'id': 'hot', 'value': 'hot', 'label': 'Hot Drinks', 'emoji': '☕', 'imgUrl': '/hot-drink.png'},
    {'id': 'cold', 'value': 'cold', 'label': 'Cold Drinks', 'emoji': '🥤', 'imgUrl': '/softdrink.png'},
    {'id': 'snacks', 'value': 'snacks', 'label': 'Snacks', 'emoji': '🍟', 'imgUrl': '/snack.png'},
    {'id': 'meals', 'value': 'meals', 'label': 'Meals', 'emoji': '🍽️', 'imgUrl': '/fried-rice.png'},
    {'id': 'sweets', 'value': 'sweets', 'label': 'Sweets', 'emoji': '🍫', 'imgUrl': '/cupcake.png'},
    {'id': 'smokes', 'value': 'smokes', 'label': 'Smokes', 'emoji': '🚬', 'imgUrl': '/cigarrete.png'},
]

PAYMENT_METHODS = ['cash', 'easypaisa', 'jazzcash', 'tab']
LOW_STOCK_THRESHOLD = 5

# Seeded on first run so a fresh install isn't an empty till.
DEFAULT_PRODUCTS = [
    ('Doodh Patti', 'hot', 120, None, '☕'), ('Green Tea', 'hot', 90, None, '🍵'),
    ('Coffee', 'hot', 180, None, '☕'), ('Kashmiri Chai', 'hot', 200, None, '🫖'),
    ('Coke 345ml', 'cold', 110, 24, '🥤'), ('Sprite 345ml', 'cold', 110, 24, '🥤'),
    ('Sting', 'cold', 100, 12, '⚡'), ('Mineral Water', 'cold', 70, 48, '💧'),
    ('Fresh Lime', 'cold', 150, None, '🍋'), ('Red Bull', 'cold', 350, 6, '🐂'),
    ('Lays Masala', 'snacks', 80, 18, '🥔'), ('Kurkure', 'snacks', 60, 22, '🌽'),
    ('Peanuts', 'snacks', 100, 15, '🥜'), ('Samosa', 'snacks', 50, 12, '🥟'),
    ('French Fries', 'snacks', 250, None, '🍟'),
    ('Chicken Roll', 'meals', 320, None, '🌯'), ('Zinger Burger', 'meals', 450, None, '🍔'),
    ('Club Sandwich', 'meals', 380, None, '🥪'), ('Chicken Karahi', 'meals', 900, None, '🍲'),
    ('Dairy Milk', 'sweets', 150, 14, '🍫'), ('Snickers', 'sweets', 180, 10, '🍫'),
    ('Ice Cream Cone', 'sweets', 130, 7, '🍦'),
    ('Marlboro', 'smokes', 480, 11, '🚬'), ('Gold Leaf', 'smokes', 420, 8, '🚬'),
    ('Lighter', 'smokes', 60, 30, '🔥'),
]


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create the folder automatically on boot if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file extension is in ALLOWED_EXTENSIONS."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def seed_canteen():
    """Populate the menu once, on an empty table."""
    if CanteenProduct.query.first():
        return
    for index, (name, category, price, stock, emoji) in enumerate(DEFAULT_PRODUCTS):
        db.session.add(CanteenProduct(name=name, category=category, price=price,
                                      stock=stock, emoji=emoji, sort_order=index))
    db.session.commit()
    print(f'  seeded: {len(DEFAULT_PRODUCTS)} canteen products')


def product_json(product):
    return {
        'id': product.id, 
        'name': product.name, 
        'category': product.category,
        'price': product.price, 
        'stock': product.stock, 
        'emoji': product.emoji,
        'imgUrl': product.img_url,
    }


def order_json(order, items=None):
    payload = {
        'id': order.id, 'code': order.order_no, 'target': order.target_label,
        'subtotal': order.subtotal, 'discountPercent': order.discount_percent,
        'discountAmount': order.discount_amount, 'total': order.total,
        # 'method' is the CHANNEL (counter vs tab); 'paymentMethod' is how the
        # money arrived. They were the same field, which is what let a
        # settlement wipe the tab marker.
        'method': order.payment_method, 'by': order.served_by,
        'status': order.status,
        'paymentStatus': order.payment_status,
        'paymentMethod': order.payment_method or '',
        'billGroup': order.bill_group,
        'khataName': order.khata_name,
        'at': order.created_at.isoformat() if order.created_at else None,
    }
    if items is not None:
        payload['items'] = [{
            'name': i.name, 'price': i.unit_price,
            'qty': i.qty, 'lineTotal': i.line_total,
        } for i in items]
        payload['itemCount'] = sum(i.qty for i in items)
    return payload


def register_canteen_routes(app, require_role, current_username, pay_link=None,
                            require_capability=None, selected_branch=None,
                            branch_scope=None, branch_report_scope=None):
    """Routes are registered against the app's own auth helpers.

    `pay_link` mints the payment URL a receipt QR points at, and
    `require_capability` gates on area of responsibility. Both are injected
    rather than imported so this module stays free of a circular import back
    into index.py.

    Every route here needs the 'canteen' capability: the canteen manager runs
    this counter, the receptionist does not.

    Passing require_role in rather than importing it keeps this module free of a
    circular import back into index.py.
    """

    @canteen_bp.route('/upload', methods=['POST'])
    def upload_image():
        require_capability('canteen')
        if 'image' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"prod_{int(datetime.now().timestamp())}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            
            # Return API-relative URL instead of static path
            return jsonify({'imgUrl': f'/canteen/media/{filename}'}), 201
        return jsonify({'error': 'Invalid file format'}), 400

    # 2. Endpoint to serve stored uploads via API
    @canteen_bp.route('/media/<path:filename>', methods=['GET'])
    def serve_canteen_media(filename):
        """Serve uploaded media directly through Flask API."""
        return send_from_directory(UPLOAD_FOLDER, filename)

    @canteen_bp.route('/products', methods=['GET'])
    def list_products():
        require_capability('canteen')
        products_q = CanteenProduct.query.filter_by(is_active=True)
        if branch_scope:
            products_q = products_q.filter(branch_scope(CanteenProduct))
        products = products_q.order_by(CanteenProduct.sort_order, CanteenProduct.id).all()
        return jsonify({
            'categories': CATEGORIES,
            'lowStockThreshold': LOW_STOCK_THRESHOLD,
            'paymentMethods': PAYMENT_METHODS,
            'products': [product_json(p) for p in products],
        })

    @canteen_bp.route('/products', methods=['POST'])
    def create_product():
        require_capability('canteen')
        data = request.json or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        try:
            price = int(data.get('price'))
        except (TypeError, ValueError):
            return jsonify({'error': 'Price must be a number'}), 400
        if price < 0:
            return jsonify({'error': 'Price cannot be negative'}), 400

        stock = data.get('stock')
        if stock in ('', None):
            stock = None                     # made to order
        else:
            try:
                stock = max(0, int(stock))
            except (TypeError, ValueError):
                return jsonify({'error': 'Stock must be a number'}), 400

        product = CanteenProduct(
            name=name,
            category=data.get('category') if data.get('category') in
            [c['id'] for c in CATEGORIES] else 'snacks',
            price=price, stock=stock,
            emoji=(data.get('emoji') or '🍽️')[:16],
            img_url=data.get('imgUrl'),
            sort_order=(db.session.query(db.func.max(CanteenProduct.sort_order)).scalar() or 0) + 1,
            branch_id=(selected_branch() if selected_branch else None),
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'product': product_json(product)}), 201

    @canteen_bp.route('/products/<int:product_id>', methods=['PATCH'])
    def update_product(product_id):
        require_capability('canteen')
        product = CanteenProduct.query.get_or_404(product_id)
        data = request.json or {}

        if 'name' in data and str(data['name']).strip():
            product.name = str(data['name']).strip()
        if 'price' in data:
            try:
                price = int(data['price'])
            except (TypeError, ValueError):
                return jsonify({'error': 'Price must be a number'}), 400
            if price < 0:
                return jsonify({'error': 'Price cannot be negative'}), 400
            product.price = price
        if 'category' in data and data['category'] in [c['id'] for c in CATEGORIES]:
            product.category = data['category']
        if 'emoji' in data:
            product.emoji = (data['emoji'] or '🍽️')[:16]
        if 'imgUrl' in data:
            product.img_url = data['imgUrl']
        if 'stock' in data:
            product.stock = None if data['stock'] in ('', None) else max(0, int(data['stock']))
        if 'restock' in data and product.stock is not None:
            product.stock = max(0, product.stock + int(data['restock']))

        db.session.commit()
        return jsonify({'product': product_json(product)})

    @canteen_bp.route('/products/<int:product_id>', methods=['DELETE'])
    def delete_product(product_id):
        require_capability('canteen')
        product = CanteenProduct.query.get_or_404(product_id)
        # Soft delete: past orders reference this row, and hard-deleting it would
        # orphan the line items on old receipts.
        product.is_active = False
        product.deleted_at = datetime.now()
        product.deleted_by = current_username()
        db.session.commit()
        return jsonify({'success': True})

    @canteen_bp.route('/orders', methods=['GET'])
    def list_orders():
        require_capability('canteen')
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_q = CanteenOrder.query.filter(CanteenOrder.created_at >= start_of_day,
                                            CanteenOrder.status == 'paid')
        recent_q = CanteenOrder.query
        if branch_report_scope:
            today_q = today_q.filter(branch_report_scope(CanteenOrder))
            recent_q = recent_q.filter(branch_report_scope(CanteenOrder))
        today = today_q.order_by(CanteenOrder.id.desc()).all()
        # Wider window than the till needs, so the analytics ranges have data.
        recent = recent_q.order_by(CanteenOrder.id.desc()).limit(500).all()

        # Line items for the orders being returned, so the ledger can say WHAT
        # was sold rather than just how many things were. One query for the
        # whole page rather than one per order.
        recent_ids = [o.id for o in recent]
        items_by_order = {}
        if recent_ids:
            for item in CanteenOrderItem.query.filter(
                    CanteenOrderItem.order_id.in_(recent_ids)).all():
                items_by_order.setdefault(item.order_id, []).append({
                    'name': item.name, 'qty': item.qty,
                    'price': item.unit_price, 'lineTotal': item.line_total,
                })

        return jsonify({
            'orders': [{
                **order_json(o),
                'items': items_by_order.get(o.id, []),
                'itemCount': sum(i['qty'] for i in items_by_order.get(o.id, [])),
                'payUrl': (pay_link(amount=o.total, kind='canteen', reference=o.order_no,
                                    payer_name=o.target_label, order_id=o.id)
                           if pay_link and o.payment_status != 'paid'
                           and o.payment_method != 'tab' and o.status != 'void' else None),
            } for o in recent],
            'todayTotal': sum(o.total for o in today),
            'todayCount': len(today),
        })
    
    @canteen_bp.route('/orders/active', methods=['GET'])
    def list_active_orders():
        require_capability('canteen')
        # Open means not yet closed — a paid order stays on the counter until
        # someone finishes with it, the same as a table bill. Voided orders are
        # not owed, and tab orders are billed with their table session.
        active_q = CanteenOrder.query.filter(CanteenOrder.closed_at.is_(None),
                                             CanteenOrder.status != 'void',
                                             CanteenOrder.payment_method != 'tab')
        if branch_scope:
            active_q = active_q.filter(branch_scope(CanteenOrder))
        recent = active_q.order_by(CanteenOrder.id.desc()).all()

        # Line items for the orders being returned, so the ledger can say WHAT
        # was sold rather than just how many things were. One query for the
        # whole page rather than one per order.
        recent_ids = [o.id for o in recent]
        items_by_order = {}
        if recent_ids:
            for item in CanteenOrderItem.query.filter(
                    CanteenOrderItem.order_id.in_(recent_ids)).all():
                items_by_order.setdefault(item.order_id, []).append({
                    'name': item.name, 'qty': item.qty,
                    'price': item.unit_price, 'lineTotal': item.line_total,
                })

        return jsonify({
            'orders': [{
                **order_json(o),
                'items': items_by_order.get(o.id, []),
                'itemCount': sum(i['qty'] for i in items_by_order.get(o.id, [])),
                'payUrl': (pay_link(amount=o.total, kind='canteen', reference=o.order_no,
                                    payer_name=o.target_label, order_id=o.id)
                           if pay_link and o.payment_status != 'paid'
                           and o.payment_method != 'tab' and o.status != 'void' else None),
            } for o in recent],
            # What's actually still owed, as opposed to merely still on screen:
            # a paid order stays listed until closed but isn't outstanding.
            'outstanding': sum(o.total for o in recent if o.payment_status != 'paid'),
            'onAccount': sum(o.total for o in recent
                             if o.payment_status != 'paid' and (o.khata_name or '').strip()),
        })


    @canteen_bp.route('/orders/<int:order_id>', methods=['GET'])
    def get_order(order_id):
        require_capability('canteen')
        order = CanteenOrder.query.get_or_404(order_id)
        items = CanteenOrderItem.query.filter_by(order_id=order.id).all()
        return jsonify({'order': order_json(order, items)})

    @canteen_bp.route('/orders', methods=['POST'])
    def create_order():
        require_capability('canteen')
        data = request.json or {}
        lines = data.get('items') or []
        if not lines:
            return jsonify({'error': 'The order is empty'}), 400

        # Collapse duplicate ids so two lines for the same product can't slip
        # past the stock check individually.
        wanted = {}
        for line in lines:
            try:
                product_id = int(line['productId'])
                qty = int(line['qty'])
            except (KeyError, TypeError, ValueError):
                return jsonify({'error': 'Malformed order line'}), 400
            if qty <= 0:
                return jsonify({'error': 'Quantities must be at least 1'}), 400
            wanted[product_id] = wanted.get(product_id, 0) + qty

        products = {p.id: p for p in
                    CanteenProduct.query.filter(CanteenProduct.id.in_(wanted.keys())).all()}

        # Check everything BEFORE writing anything, so a rejected order can't
        # leave half the shelf decremented.
        for product_id, qty in wanted.items():
            product = products.get(product_id)
            if not product or not product.is_active:
                return jsonify({'error': 'One of those items is no longer available'}), 400
            if product.stock is not None and qty > product.stock:
                return jsonify({
                    'error': f'Only {product.stock} × {product.name} left',
                    'productId': product_id,
                }), 409

        try:
            discount_percent = int(data.get('discountPercent') or 0)
        except (TypeError, ValueError):
            discount_percent = 0
        discount_percent = min(max(discount_percent, 0), 100)

        subtotal = sum(products[pid].price * qty for pid, qty in wanted.items())
        discount_amount = round(subtotal * discount_percent / 100)
        total = subtotal - discount_amount

        method = data.get('method') if data.get('method') in PAYMENT_METHODS else 'cash'

        table_uid = data.get('tableUid') or None
        session_id = None
        target = 'Walk-in'
        if table_uid:
            table = PoolTable.query.filter_by(uid=table_uid).first()
            if not table:
                return jsonify({'error': 'That station no longer exists'}), 404
            session_id = table.session_id
            target = f'{table.table_type.title()} #{table.table_id}'

        # Putting it on the tab only means something while a tab is open. Without
        # these the charge would be recorded against nothing and never billed.
        # Order matters: no station at all is a different mistake from a station
        # that simply isn't running.
        if method == 'tab' and not table_uid:
            return jsonify({'error': 'Pick a station to charge the tab to'}), 400
        if method == 'tab' and not session_id:
            return jsonify({
                'error': 'That station has no running session to charge to',
            }), 409

        sequence = (db.session.query(db.func.max(CanteenOrder.id)).scalar() or 1000) + 1
        order = CanteenOrder(
            branch_id=(selected_branch() if selected_branch else None),
            order_no=f'C-{sequence}', target_label=target, table_uid=table_uid,
            session_id=session_id, subtotal=subtotal,
            discount_percent=discount_percent, discount_amount=discount_amount,
            total=total, payment_method=method, served_by=current_username(),
            status='paid',
            # A tab rides the session bill and is settled when play ends; a
            # counter sale is unpaid until the receipt is marked paid.
            payment_status='pending',
        )
        db.session.add(order)
        db.session.flush()

        items = []
        for product_id, qty in wanted.items():
            product = products[product_id]
            item = CanteenOrderItem(
                order_id=order.id, product_id=product.id, name=product.name,
                unit_price=product.price, qty=qty,
                line_total=product.price * qty,
            )
            db.session.add(item)
            items.append(item)
            if product.stock is not None:
                product.stock = max(0, product.stock - qty)

        db.session.commit()

        payload = order_json(order, items)
        # Counter sales are paid now, so the receipt needs its QR immediately.
        # A tab order is settled with the table session and has nothing to pay.
        if order.payment_method != 'tab':
            payload['payUrl'] = pay_link(
                amount=order.total, kind='canteen',
                reference=order.order_no, payer_name=order.target_label,
                order_id=order.id,
            )
        return jsonify({'order': payload}), 201

    @canteen_bp.route('/orders/<int:order_id>/status', methods=['GET'])
    def canteen_order_status(order_id):
        """Settlement state of one order.

        The open receipt polls this so a QR payment shows up on its own, the
        same way a table bill does. It cannot rely on the payment-notification
        feed: those are consumed by whichever screen reads them first.
        """
        require_capability('canteen')
        order = CanteenOrder.query.get_or_404(order_id)
        return jsonify({
            'id': order.id,
            'paymentStatus': order.payment_status,
            'paymentMethod': order.payment_method or '',
            'khataName': order.khata_name,
            'status': order.status,
        })

    @canteen_bp.route('/orders/<int:order_id>/settle', methods=['POST'])
    def settle_canteen_order(order_id):
        """Mark a counter sale paid, or put it on somebody's khata."""
        require_capability('canteen')
        order = CanteenOrder.query.get_or_404(order_id)
        if order.status == 'void':
            return jsonify({'error': 'That order was voided'}), 409
        # Tab orders are settled with the session, not here.
        if order.payment_method == 'tab':
            return jsonify({'error': 'This is billed with the table session'}), 409

        data = request.json or {}
        status = data.get('status')
        if status == 'paid':
            # Already settled — almost always a QR payment that landed while the
            # receipt was open. Overwriting it would replace the real method
            # with 'cash' and record money that never reached the drawer.
            if order.payment_status == 'paid':
                return jsonify({
                    'id': order.id, 'paymentStatus': 'paid',
                    'paymentMethod': order.payment_method or '',
                    'alreadyPaid': True,
                })
            method = data.get('method')
            order.payment_method = method if method in (
                'cash', 'easypaisa', 'jazzcash', 'account') else 'cash'
            order.payment_status = 'paid'
            order.settled_at = datetime.now()
            order.khata_name = None
        elif status == 'pending':
            order.payment_status = 'pending'
            order.payment_method = ''
            order.settled_at = None
            order.khata_name = None
        elif status == 'khata':
            name = (data.get('name') or '').strip()
            if not name:
                return jsonify({'error': 'A khata needs a name'}), 400
            order.payment_status = 'pending'
            order.khata_name = name
            order.settled_at = None
        else:
            return jsonify({'error': 'Status must be paid, pending or khata'}), 400

        db.session.commit()
        return jsonify({'id': order.id, 'paymentStatus': order.payment_status,
                        'paymentMethod': order.payment_method or '',
                        'khataName': order.khata_name})

    @canteen_bp.route('/orders/<int:order_id>/close', methods=['POST'])
    def close_canteen_order(order_id):
        """Finish with a counter sale: take it off the Active Bills page.

        Mirrors closing a table bill. Only a settled order can be closed —
        paid, or placed on somebody's account — otherwise closing would be a
        way to make an unpaid order disappear from every screen at once, which
        is exactly what that page exists to prevent.
        """
        require_capability('canteen')
        order = CanteenOrder.query.get_or_404(order_id)

        if order.status == 'void':
            return jsonify({'error': 'That order was voided'}), 409

        # A tab order is closed with its table bill, never on its own, or the
        # two halves of one guest's bill could end up in different states.
        if order.payment_method == 'tab':
            return jsonify({'error': 'This is billed with the table session'}), 409

        settled = order.payment_status == 'paid' or bool((order.khata_name or '').strip())
        if not settled:
            return jsonify({
                'error': 'Take payment, or put this on an account, before closing it',
            }), 409

        if order.closed_at:
            return jsonify({'id': order.id, 'alreadyClosed': True,
                            'closedAt': order.closed_at.isoformat()})

        order.closed_at = datetime.now()
        order.closed_by = current_username()
        db.session.commit()
        return jsonify({
            'id': order.id,
            'closedAt': order.closed_at.isoformat(),
            'closedBy': order.closed_by,
        })

    @canteen_bp.route('/orders/<int:order_id>/reopen', methods=['POST'])
    def reopen_canteen_order(order_id):
        """Put a closed order back on the counter — a closure was a mistake."""
        require_role('manager')
        order = CanteenOrder.query.get_or_404(order_id)
        order.closed_at = None
        order.closed_by = None
        db.session.commit()
        return jsonify({'id': order.id, 'reopened': True})

    @canteen_bp.route('/orders/<int:order_id>/void', methods=['POST'])
    def void_order(order_id):
        """Reverse a mistaken sale and put the stock back on the shelf."""
        require_capability('canteen')
        order = CanteenOrder.query.get_or_404(order_id)
        if order.status == 'void':
            return jsonify({'error': 'Already voided'}), 409

        for item in CanteenOrderItem.query.filter_by(order_id=order.id).all():
            product = CanteenProduct.query.get(item.product_id) if item.product_id else None
            if product and product.stock is not None:
                product.stock += item.qty

        order.status = 'void'
        db.session.commit()
        return jsonify({'success': True})

    app.register_blueprint(canteen_bp)