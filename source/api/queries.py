from flask import request, jsonify, current_app
from source.services.document_service import DocumentService
from source.services.weaviate_service import WeaviateService
from source.services.embedding_service import EmbeddingService
from source.utils.config import Config

def register_routes(app):
    @app.route('/queries', methods=['POST'])  # Changed to POST
    def query_document_route():
        # Get document_id and query_text from the request body (JSON)
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Missing request body'}), 400

        document_id = data.get('document_id')
        query_text = data.get('query')

        if not document_id:
            return jsonify({'error': 'Missing document_id'}), 400
        if not query_text:
            return jsonify({'error': 'Missing query parameter'}), 400

        config = Config()
        embedding_service = EmbeddingService(use_gemini=True, model_name=config.HUGGINGFACE_MODEL_NAME) #Changed to use openai
        weaviate_service = WeaviateService(config)
        document_service = DocumentService(embedding_service, weaviate_service, config)

        try:
            results = document_service.query_document(document_id, query_text)
            return jsonify([r.__dict__ for r in results]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500