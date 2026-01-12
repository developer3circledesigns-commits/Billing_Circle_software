from flask import Blueprint, render_template

purchase_orders_bp = Blueprint('purchase_orders', __name__, url_prefix='/purchase-orders')

@purchase_orders_bp.route('/')
def list_purchase_orders():
    return render_template('purchase_order_templates/list.html')

@purchase_orders_bp.route('/add')
def add_purchase_order():
    return render_template('purchase_order_templates/form.html', mode='add')

@purchase_orders_bp.route('/edit/<po_id>')
def edit_purchase_order(po_id):
    return render_template('purchase_order_templates/form.html', mode='edit', po_id=po_id)

@purchase_orders_bp.route('/view/<po_id>')
def view_purchase_order(po_id):
    return render_template('purchase_order_templates/view.html', po_id=po_id)
