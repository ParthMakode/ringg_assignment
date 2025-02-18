import os
from google import genai
from google.genai import types
# from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
class EmbeddingService:
    def __init__(self, use_gemini=False, model_name=None):
        load_dotenv()
        self.use_gemini = use_gemini
        self.client=None
        if use_gemini:
            client = genai.Client(api_key="AIzaSyDivK7EMR5Z8qGLVNJaCVUPHDFZUC2kh-8")
            
            self.client=client
            
            
        # else:
        #     self.hf_model = SentenceTransformer(model_name)
            

    def generate_embedding(self, text: str) -> list[float]:
        if self.use_gemini:
            result = self.client.models.embed_content(
                model="text-embedding-004", contents=text
            )
            return result.embeddings[0].values
        # else:
        #     return self.hf_model.encode(text).tolist()

