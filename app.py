from flask import Flask, jsonify
from flask_cors import CORS
from db import create_indexes
from blueprints.auth import auth_bp
from blueprints.locations import locations_bp
from blueprints.forecasts import forecasts_bp
from blueprints.observations import observations_bp
from blueprints.analytics import analytics_bp
from blueprints.tracker import tracker_bp
from blueprints.alerts import alerts_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    for bp in (auth_bp, locations_bp, forecasts_bp, observations_bp,
               analytics_bp, tracker_bp, alerts_bp):
        app.register_blueprint(bp, url_prefix="/api/v1")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def bad_method(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app

if __name__ == "__main__":
    create_indexes()
create_app().run(debug=True, port=5001, use_reloader=False)