from flask import Flask, render_template
import logging
from app.config import Config
from app.db import db
from app.services import init_dsa_structures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Database Schema & Seeds
    with app.app_context():
        db.init_database()
        init_dsa_structures()

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.book_routes import book_bp
    from app.routes.student_routes import student_bp
    from app.routes.issue_routes import issue_bp
    from app.routes.reservation_routes import reservation_bp
    from app.routes.recommendation_routes import recommendation_bp
    from app.routes.dsa_lab_routes import dsa_lab_bp
    from app.routes.report_routes import report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(book_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(issue_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(dsa_lab_bp)
    app.register_blueprint(report_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', page_title='Page Not Found', error_message='The requested page could not be found.'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('base.html', page_title='Internal Server Error', error_message='An unexpected error occurred.'), 500

    return app
