from flask import request, jsonify, current_app
from source.services.document_service import DocumentService
from source.services.weaviate_service import WeaviateService
from source.services.embedding_service import EmbeddingService
from source.utils.config import Config

# No Blueprint needed

def register_routes(app):
    @app.route('/queries/<document_id>', methods=['GET'])
    def query_document_route(document_id):
        query_text = request.args.get('query')
        if not query_text:
            return jsonify({'error': 'Missing query parameter'}), 400

        config = Config()
        embedding_service = EmbeddingService(use_gemini=True, model_name=config.HUGGINGFACE_MODEL_NAME)
        weaviate_service = WeaviateService(config)
        document_service = DocumentService(embedding_service, weaviate_service, config)

        try:
            results = document_service.query_document(document_id, query_text)
            return jsonify([r.__dict__ for r in results]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
