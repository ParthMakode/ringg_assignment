from flask import Flask
from source.utils.config import Config
import os
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions (if any) here

    # Register blueprints (API routes)
    from source.api.documents import documents_bp
    from source.api.queries import queries_bp
    app.register_blueprint(documents_bp)
    app.register_blueprint(queries_bp)
    
    return app 

if __name__ == '__main__':
    flask_app = create_app()
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']

    flask_app.run(host=host, port=port, debug=debug)
    