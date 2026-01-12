from flask import Blueprint, render_template

weavers_bp = Blueprint('weavers', __name__, url_prefix='/weavers')

@weavers_bp.route('/')
def list_weavers():
    return render_template('weavers/list.html')

@weavers_bp.route('/add')
def add_weaver():
    return render_template('weavers/form.html', mode='add')

@weavers_bp.route('/edit/<weaver_id>')
def edit_weaver(weaver_id):
    return render_template('weavers/form.html', mode='edit', weaver_id=weaver_id)

@weavers_bp.route('/view/<weaver_id>')
def view_weaver(weaver_id):
    return render_template('weavers/view.html', weaver_id=weaver_id)
