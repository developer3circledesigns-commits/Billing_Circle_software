from flask import Blueprint, render_template

vendor_payments_bp = Blueprint('vendor_payments', __name__, url_prefix='/vendor-payments')

@vendor_payments_bp.route('/')
def list_vendor_payments():
    return render_template('vendor_payments/list.html')

@vendor_payments_bp.route('/add')
def add_vendor_payment():
    return render_template('vendor_payments/form.html')

@vendor_payments_bp.route('/add-for-bill/<bill_id>')
def add_payment_for_bill(bill_id):
    return render_template('vendor_payments/form.html', bill_id=bill_id)

@vendor_payments_bp.route('/view/<payment_id>')
def view_vendor_payment(payment_id):
    return render_template('vendor_payments/view.html', payment_id=payment_id)
