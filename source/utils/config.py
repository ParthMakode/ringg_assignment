import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class Config:
    WEAVIATE_URL = os.environ.get('WEAVIATE_URL')
    WEAVIATE_API_KEY = os.environ.get('WEAVIATE_API_KEY')  # Optional, if needed
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') # If using GEMINI for embeddings
    HUGGINGFACE_MODEL_NAME = os.environ.get('HUGGINGFACE_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2') # Default to a good general-purpose model
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'data/uploads')
    LLAMA_PARSE_API=os.environ.get('LLAMA_CLOUD_API_KEY')
    # Add other configurations as needed (e.g., chunk size, overlap)
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 10