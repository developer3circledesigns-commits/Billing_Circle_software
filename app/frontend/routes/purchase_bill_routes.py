from flask import Blueprint, render_template

purchase_bills_bp = Blueprint('purchase_bills', __name__, url_prefix='/purchase-bills')

@purchase_bills_bp.route('/')
def list_purchase_bills():
    return render_template('purchase_bill_templates/list.html')

@purchase_bills_bp.route('/add')
def add_purchase_bill():
    return render_template('purchase_bill_templates/form.html', mode='add')

@purchase_bills_bp.route('/add-from-po/<po_id>')
def add_bill_from_po(po_id):
    return render_template('purchase_bill_templates/form.html', mode='add', po_id=po_id)

@purchase_bills_bp.route('/edit/<bill_id>')
def edit_purchase_bill(bill_id):
    return render_template('purchase_bill_templates/form.html', mode='edit', bill_id=bill_id)

@purchase_bills_bp.route('/view/<bill_id>')
def view_purchase_bill(bill_id):
    return render_template('purchase_bill_templates/view.html', bill_id=bill_id)
