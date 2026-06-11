import os
from pathlib import Path

from flask import Flask

from app.config import config_by_name
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG") or os.environ.get(
            "FLASK_ENV", "development"
        )

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.recruiter import recruiter_bp
    from app.routes.candidate import candidate_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(recruiter_bp, url_prefix="/recruiter")
    app.register_blueprint(candidate_bp, url_prefix="/candidate")

    @app.context_processor
    def inject_globals():
        return {"app_name": "Mr. Hyre"}

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template

        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template

        return render_template("errors/404.html"), 404

    return app
