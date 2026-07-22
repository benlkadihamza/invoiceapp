from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.transactions import transactions_bp
from routes.persons import persons_bp
from routes.categories import categories_bp
from routes.reports import reports_bp
from routes.statistics import statistics_bp
from routes.exports import exports_bp
from routes.invoices import invoices_bp
from routes.stock import stock_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(persons_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(statistics_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(stock_bp)

