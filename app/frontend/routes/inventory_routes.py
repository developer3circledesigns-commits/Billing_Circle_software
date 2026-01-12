from flask import Blueprint, render_template

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/live-stocks')
def live_stocks():
    return render_template('inventory/live_stocks.html')

@inventory_bp.route('/categories')
def categories_list():
    return render_template('categories/list.html')

@inventory_bp.route('/items')
def items_list():
    return render_template('items/list.html')

@inventory_bp.route('/items/add')
def add_item():
    return render_template('items/form.html', mode='add')

@inventory_bp.route('/items/edit/<item_id>')
def edit_item(item_id):
    return render_template('items/form.html', mode='edit', item_id=item_id)

@inventory_bp.route('/items/view/<item_id>')
def view_item(item_id):
    return render_template('items/view.html', item_id=item_id)
