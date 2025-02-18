import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class Config:
    WEAVIATE_URL = os.environ.get('WEAVIATE_URL')
    WEAVIATE_API_KEY = os.environ.get('WEAVIATE_API_KEY')  # Optional, if needed
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') # If using OpenAI
    HUGGINGFACE_MODEL_NAME = os.environ.get('HUGGINGFACE_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2') # Default to a good general-purpose model
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'data/uploads')
    # Add other configurations as needed (e.g., chunk size, overlap)
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50