from flask import Blueprint, request, jsonify, current_app
from ..services.document_service import DocumentService
from ..services.weaviate_service import WeaviateService
from ..services.embedding_service import EmbeddingService
from ..utils.config import Config

queries_bp = Blueprint('queries', __name__, url_prefix='/queries')

@queries_bp.route('/<document_id>', methods=['GET'])
def query_document_route(document_id):
    query_text = request.args.get('query')
    if not query_text:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    config = Config()
    embedding_service = EmbeddingService(use_openai=False, model_name= config.HUGGINGFACE_MODEL_NAME)  # Or True for OpenAI
    weaviate_service = WeaviateService(config)
    document_service = DocumentService(embedding_service, weaviate_service, config)

    try:
        results = document_service.query_document(document_id, query_text)
        return jsonify([r.__dict__ for r in results]), 200  # Convert dataclass to dict
    except Exception as e:
            return jsonify({'error': str(e)}), 500