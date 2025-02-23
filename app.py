from flask import Flask
from source.utils.config import Config
from source.api.documents import register_routes as register_document_routes
from source.api.queries import register_routes as register_query_routes
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register routes directly (no blueprints)
    register_document_routes(app)
    register_query_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()  # Use consistent variable name 'app'
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']

    app.run(host=host, port=port, debug=debug)
    
    
    
    
    
    # TODO : implement json , better chunking for file types, argument for top ten results
    