from flask import Blueprint, render_template

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
def customers_list():
    return render_template('customers/list.html')

@customers_bp.route('/add')
def add_customer():
    return render_template('customers/form.html', mode='add')

@customers_bp.route('/edit/<customer_id>')
def edit_customer(customer_id):
    return render_template('customers/form.html', mode='edit', customer_id=customer_id)

@customers_bp.route('/view/<customer_id>')
def view_customer(customer_id):
    return render_template('customers/view.html', customer_id=customer_id)
