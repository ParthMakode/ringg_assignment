from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os ,json
from source.services.document_service import DocumentService
from source.services.weaviate_service import WeaviateService
from source.services.embedding_service import EmbeddingService
from source.utils.config import Config

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

@documents_bp.route('', methods=['POST'])
def upload_document():
    #check if the post request has file
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']

    #if user does not select any file.
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        content_type = file.content_type
        metadata = request.form.get('metadata') # Get metadata if present
        if metadata:
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                return jsonify({'error': "Invalid metadata format, must be valid JSON"}), 400
        
        # Save the file temporarily
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        #initialize necessary services.
        config = Config()
        embedding_service = EmbeddingService(use_openai=False, model_name=config.HUGGINGFACE_MODEL_NAME)  # Or True for OpenAI
        weaviate_service = WeaviateService(config)
        document_service = DocumentService(embedding_service, weaviate_service, config)

        try:
            document_id = document_service.process_and_index_document(file_path, filename, content_type, metadata)
            return jsonify({'message': 'Document uploaded and processed', 'document_id': document_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            os.remove(file_path) 

@documents_bp.route('/<document_id>', methods=['PUT'])
def update_document_route(document_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        content_type = file.content_type
        metadata = request.form.get('metadata')
        if metadata:
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                return jsonify({'error': "Invalid metadata format, must be valid JSON"}), 400

        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        config = Config()
        embedding_service = EmbeddingService(use_openai=False, model_name=config.HUGGINGFACE_MODEL_NAME)
        weaviate_service = WeaviateService(config)
        document_service = DocumentService(embedding_service, weaviate_service, config)

        try:
            document_id = document_service.update_document(document_id, file_path, filename, content_type, metadata)
            return jsonify({'message': 'Document updated and processed', 'document_id': document_id}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            os.remove(file_path)

@documents_bp.route('/<document_id>', methods=['DELETE'])
def delete_document_route(document_id):
    config = Config()
    embedding_service = EmbeddingService(use_openai=False, model_name=config.HUGGINGFACE_MODEL_NAME)  # Or True for OpenAI
    weaviate_service = WeaviateService(config)
    document_service = DocumentService(embedding_service, weaviate_service, config)

    try:
        document_service.delete_document(document_id)
        return jsonify({'message': f'Document with id {document_id} deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500