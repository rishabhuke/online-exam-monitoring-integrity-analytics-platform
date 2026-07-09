from flask import Flask, jsonify, redirect, url_for
from config import Config
import database
from auth import auth_bp

def create_app() -> Flask:
    """Application factory for the Candidate Authentication Backend."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize SQLite database schema
    database.init_db()

    # Register Authentication Blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Root route - helper redirection to login template
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Global Error Handlers returning clean JSON responses
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "status": "error",
            "message": "Resource not found"
        }), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "status": "error",
            "message": "An internal server error occurred"
        }), 500

    return app

if __name__ == '__main__':
    flask_app = create_app()
    # Runs locally on port 5000
    flask_app.run(host='127.0.0.1', port=5000, debug=True)
