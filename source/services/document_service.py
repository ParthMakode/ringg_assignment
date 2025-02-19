import uuid
from source.utils.file_utils import read_and_parse_file
from source.services.embedding_service import EmbeddingService
from source.services.weaviate_service import WeaviateService
from source.models import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from source.utils.config import Config

class DocumentService:
    def __init__(self, embedding_service: EmbeddingService, weaviate_service: WeaviateService, config: Config):
        self.embedding_service = embedding_service
        self.weaviate_service = weaviate_service
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            length_function=len
        )


    def process_and_index_document(self, file_path: str, file_name:str, content_type: str, metadata: dict = None) -> str:
        """Reads, parses, chunks, embeds, and indexes a document."""
        try:
            file_content = read_and_parse_file(file_path, content_type)
        except Exception as e:
            raise ValueError(f"Error Processing file: {e}")

        # Generate a unique ID for the document
        document_id = str(uuid.uuid4())
        document = Document(id=document_id, filename=file_name, content=file_content, content_type=content_type, metadata=metadata or {})

        if content_type != "application/json": # Chunk all except json.
            chunks = self.text_splitter.split_text(file_content)
            document.content = chunks
        else:
            chunks = [file_content] #dont chunk.

        embeddings = [self.embedding_service.generate_embedding(chunk) for chunk in chunks]
        self.weaviate_service.index_document(document, embeddings)
        return document_id

    def update_document(self, document_id: str, file_path: str, file_name:str, content_type: str, metadata: dict = None) -> str:
        """Deletes the old document and indexes the new one."""
        self.delete_document(document_id)
        return self.process_and_index_document(file_path, file_name, content_type, metadata)


    def delete_document(self, document_id: str):
        """Deletes a document from Weaviate."""
        self.weaviate_service.delete_document(document_id)

    def query_document(self, document_id: str, query_text: str) -> list:
        """Generates an embedding for the query and queries Weaviate."""
        query_embedding = self.embedding_service.generate_embedding(query_text)
        return self.weaviate_service.query_document(document_id, query_embedding)