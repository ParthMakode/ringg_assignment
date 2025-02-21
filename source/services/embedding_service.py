import os
from google import genai
from google.genai import types
# from sentence_transformers import SentenceTransformer
from source.utils.config import Config
class EmbeddingService:
    def __init__(self, use_gemini=False, model_name=None):
        self.use_gemini = use_gemini
        self.client=None
        if use_gemini:
            client = genai.Client(api_key=Config.GEMINI_API_KEY)
            
            self.client=client
            
        print("embedder initialised")
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

