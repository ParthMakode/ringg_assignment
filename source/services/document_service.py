import uuid,time
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


    def process_and_index_document(self, file_path: str, file_name:str, content_type: str, metadata: dict = None,oldid:str=None) -> str:
        """Reads, parses, chunks, embeds, and indexes a document."""
        try:
            print("file path ",file_path)
            file_content = read_and_parse_file(file_path, content_type)
        except Exception as e:
            print(f"Error Processing file: {e}")
            raise ValueError(f"Error Processing file: {e}")

        # Generate a unique ID for the document
        print("oldid ",oldid)
        document_id = str(uuid.uuid4())
        if(oldid is not None):
            document_id=oldid
        print("id generated")
        document = Document(id=document_id, filename=file_name, content=file_content, content_type=content_type, metadata=metadata or {})
        print("chunking")
        
        if content_type != "application/json": # Chunk all except json.
            chunks = self.text_splitter.split_text(file_content)
            document.content = chunks
        else:
            chunks = [file_content]
            document.content=chunks#dont chunk.
        print("chunking done")
        embeddings = [self.embedding_service.generate_embedding(chunk) for chunk in chunks]
        print("reached before weaviate call")
        self.weaviate_service.index_document(document, embeddings)
        return document_id

    def update_document(self, document_id: str, file_path: str, file_name:str, content_type: str, metadata: dict = None) -> str:
        """Deletes the old document and indexes the new one."""
        old_id=self.delete_document(document_id)
        print("deleted document id ",document_id,"\nrenewing new document with ",document_id,"\n",file_path)
        return self.process_and_index_document(file_path, file_name, content_type, metadata,oldid=old_id)


    def delete_document(self, document_id: str):
        """Deletes a document from Weaviate."""
        return self.weaviate_service.delete_document(document_id)

    def query_document(self, document_id: str, query_text: str) -> list:
        """Generates an embedding for the query and queries Weaviate."""
        query_embedding = self.embedding_service.generate_embedding(query_text)
        return self.weaviate_service.query_document(document_id, query_embedding)