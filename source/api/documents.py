from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
from source.services.document_service import DocumentService
from source.services.weaviate_service import WeaviateService
from source.services.embedding_service import EmbeddingService
from source.utils.config import Config

def register_routes(app):

    @app.route('/documents', methods=['POST'])
    def handle_document():
        """Handles document upload, update, and deletion via a single POST endpoint."""

        # Determine the action (upload, update, delete)
        action = request.form.get('action')
        document_id = request.form.get('document_id')  # Get document_id from form data

        if action == 'upload':
            # --- Upload Logic ---
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['file']

            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            filename = secure_filename(file.filename)
            content_type = request.form.get('content_type')  # Get from form data
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
            embedding_service = EmbeddingService(use_gemini=True, model_name=config.HUGGINGFACE_MODEL_NAME)
            weaviate_service = WeaviateService(config)
            document_service = DocumentService(embedding_service, weaviate_service, config)

            try:
                document_id = document_service.process_and_index_document(file_path, filename, content_type, metadata)
                return jsonify({'message': 'Document uploaded and processed', 'document_id': document_id}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                os.remove(file_path)

        elif action == 'update':
            # --- Update Logic ---
            if not document_id:
                return jsonify({'error': 'Missing document_id for update'}), 400
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['file']

            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            filename = secure_filename(file.filename)
            content_type = request.form.get('content_type') # Get from form data
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
            embedding_service = EmbeddingService(use_gemini=True, model_name=config.HUGGINGFACE_MODEL_NAME)
            weaviate_service = WeaviateService(config)
            document_service = DocumentService(embedding_service, weaviate_service, config)

            try:
                document_id = document_service.update_document(document_id, file_path, filename, content_type, metadata)
                return jsonify({'message': 'Document updated and processed', 'document_id': document_id}), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                os.remove(file_path)
        elif action == 'delete':
            # --- Delete Logic ---
            if not document_id:
                return jsonify({'error': 'Missing document_id for delete'}), 400

            config = Config()
            embedding_service = EmbeddingService(use_gemini=True, model_name=config.HUGGINGFACE_MODEL_NAME)
            weaviate_service = WeaviateService(config)
            document_service = DocumentService(embedding_service, weaviate_service, config)

            try:
                document_service.delete_document(document_id)
                return jsonify({'message': f'Document with id {document_id} deleted'}), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        else:
            return jsonify({'error': 'Invalid action specified'}), 400