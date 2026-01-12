from flask import Flask, send_from_directory
import os
from app.core.config import settings

def create_app():
    app = Flask(__name__, 
                template_folder='templates', 
                static_folder='static')
    
    app.secret_key = settings.SECRET_KEY
    app.config['API_URL'] = os.getenv('APP_API_URL', 'http://127.0.0.1:8000/api/v1')
    
    # Register Blueprints
    from app.frontend.routes.auth_routes import auth_bp
    from app.frontend.routes.dashboard_routes import dashboard_bp
    from app.frontend.routes.inventory_routes import inventory_bp
    from app.frontend.routes.sales_routes import sales_bp
    from app.frontend.routes.weaver_routes import weavers_bp
    from app.frontend.routes.management_routes import management_bp
    from app.frontend.routes.customer_routes import customers_bp
    from app.frontend.routes.purchase_order_routes import purchase_orders_bp
    from app.frontend.routes.purchase_bill_routes import purchase_bills_bp
    from app.frontend.routes.vendor_payment_routes import vendor_payments_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(weavers_bp)
    app.register_blueprint(management_bp)
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(purchase_orders_bp)
    app.register_blueprint(purchase_bills_bp)

    app.register_blueprint(vendor_payments_bp)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                                   'Logo.png', mimetype='image/vnd.microsoft.icon')
    
    return app
