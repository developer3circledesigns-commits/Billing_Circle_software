from flask import Blueprint, render_template

management_bp = Blueprint('management', __name__)

@management_bp.route('/organization')
def organization():
    return render_template('management/organization.html')

@management_bp.route('/organization/members')
def organization_members():
    return render_template('management/users.html', role='member')

@management_bp.route('/users/<role>')
def users_list(role):
    return render_template('management/users.html', role=role)

@management_bp.route('/reports')
def reports():
    return render_template('management/reports.html')

@management_bp.route('/settings')
def settings_page():
    return render_template('management/settings.html')

@management_bp.route('/profile')
def profile():
    return render_template('management/profile.html')

@management_bp.route('/subscription')
def subscription():
    return render_template('management/subscription.html')
