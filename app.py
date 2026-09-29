# app.py
from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from config import Config
from models import db, bcrypt
from auth import login_required

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    CORS(app)

    # Register blueprints
    from routes.auth_routes import bp as auth_bp
    from routes.swap_routes import bp as swap_bp
    from routes.route_routes import bp as route_bp
    from routes.analytics_routes import bp as analytics_bp
    from routes.llm_routes import bp as llm_bp
    from routes.admin_routes import bp as admin_bp
    from routes.station_routes import bp as station_bp
    from routes.fleet_routes import bp as fleet_bp
    from routes.rider_routes import bp as rider_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(swap_bp)
    app.register_blueprint(route_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(llm_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(station_bp)
    app.register_blueprint(fleet_bp)
    app.register_blueprint(rider_bp)

    # --- Frontend routes ---
    @app.route("/")
    def index():
        return send_from_directory("templates", "index.html")

    @app.route("/admin")
    def admin_page():
        return send_from_directory("templates", "admin.html")

    @app.route("/station")
    def station_page():
        return send_from_directory("templates", "station.html")

    @app.route("/fleet")
    def fleet_page():
        return send_from_directory("templates", "fleet.html")

    @app.route("/rider")
    def rider_page():
        return send_from_directory("templates", "rider.html")

    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory("static", filename)

    # --- Health ---
    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "service": "MAPNA SwapFleet AI"})

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"ok": False, "error": "not_found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500
    @app.get("/")
    def read_root():
        return {"Python": "on Vercel"}
    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)