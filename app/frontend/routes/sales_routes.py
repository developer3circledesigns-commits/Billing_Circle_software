from flask import Blueprint, render_template

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/quotations')
def quotations_list():
    return render_template('sales/quotations_list.html')

@sales_bp.route('/quotations/create')
def quotation_create():
    return render_template('sales/quotation_form.html')

@sales_bp.route('/quotations/view/<id>')
def quotation_view(id):
    return render_template('sales/quotation_view.html', quote_id=id)

@sales_bp.route('/quotations/edit/<id>')
def quotation_edit(id):
    return render_template('sales/quotation_form.html', quote_id=id)

@sales_bp.route('/invoices')
def invoices_list():
    return render_template('sales/invoices_list.html')

@sales_bp.route('/invoices/create')
def invoice_create():
    return render_template('sales/invoice_form.html')

@sales_bp.route('/invoices/edit/<id>')
def invoice_edit(id):
    return render_template('sales/invoice_form.html', invoice_id=id)

@sales_bp.route('/invoices/view/<id>')
def invoice_view(id):
    return render_template('sales/invoice_view.html', invoice_id=id)

@sales_bp.route('/payments/history')
def payments_history():
    return render_template('payments/history.html')

