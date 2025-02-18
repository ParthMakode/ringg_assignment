from flask import Flask
from .utils.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions (if any) here

    # Register blueprints (API routes)
    from .api.documents import documents_bp
    from .api.queries import queries_bp
    app.register_blueprint(documents_bp)
    app.register_blueprint(queries_bp)

    return app