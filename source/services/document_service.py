import uuid,time,json
from source.utils.file_utils import read_and_parse_file
from source.services.embedding_service import EmbeddingService
from source.services.weaviate_service import WeaviateService
from source.models import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from source.utils.config import Config
from typing import List, Dict, Any,Tuple

class DocumentService:
    def __init__(self, embedding_service: EmbeddingService, weaviate_service: WeaviateService, config: Config):
        self.embedding_service = embedding_service
        self.weaviate_service = weaviate_service
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=['.'],
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            length_function=len
        )
        
    # def hierarchical_chunk_json(self, json_data: Any) -> Tuple[List[str], List[str]]:
    #     """
    #     Recursively parse hierarchical JSON and produce two lists:
    #      - chunks: text representations of each leaf node (with their hierarchical path).
    #      - hierarchy_paths: the hierarchical keys corresponding to each chunk.
    #     """
    #     chunks = []
    #     hierarchy_paths = []

    #     def recursive_parse(data: Any, path: str = ""):
    #         if isinstance(data, dict):
    #             for key, value in data.items():
    #                 new_path = f"{path}.{key}" if path else key
    #                 if isinstance(value, (dict, list)):
    #                     recursive_parse(value, new_path)
    #                 else:
    #                     chunk = f"{new_path}: {value}"
    #                     chunks.append(chunk)
    #                     hierarchy_paths.append(new_path)
    #         elif isinstance(data, list):
    #             for idx, item in enumerate(data):
    #                 new_path = f"{path}[{idx}]"
    #                 if isinstance(item, (dict, list)):
    #                     recursive_parse(item, new_path)
    #                 else:
    #                     chunk = f"{new_path}: {item}"
    #                     chunks.append(chunk)
    #                     hierarchy_paths.append(new_path)

    #     recursive_parse(json_data)
    #     return chunks, hierarchy_paths

    def chunk_pdf_docx(self,text: str) -> list[str]:    
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_chunks = markdown_splitter.split_text(text)

        final_chunks = []
        for chunk in md_chunks:
            if len(chunk.page_content) <= self.config.CHUNK_SIZE:
                final_chunks.append(chunk.page_content)
            else:
                smaller_chunks = self.text_splitter.split_text(chunk.page_content)
                final_chunks.extend(smaller_chunks)

        return final_chunks

    

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
        
        if (content_type == "application/pdf" or content_type =="application/vnd.openxmlformats-officedocument.wordprocessingml.document"): # seperate chunking for pdf and docx cause most prolly will get markdown chunking.
            chunks = self.chunk_pdf_docx(file_content)
            document.content = chunks
        elif (content_type == "text/plain"):
            chunks = self.text_splitter.split_text(file_content)
            document.content = chunks
        else:# json case
            # chunks, hierarchy_paths=self.hierarchical_chunk_json(json.loads(file_content))
            # embeddings = [self.embedding_service.generate_embedding(chunk) for chunk in chunks]
            # self.weaviate_service.index_json_document(document,chunks,hierarchy_paths,embeddings)
            chunks=[file_content]
            document.content=chunks
            
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

    def query_document(self, document_id: str, query_text: str,limit:int=5) -> list:
        """Generates an embedding for the query and queries Weaviate."""
        query_embedding = self.embedding_service.generate_embedding(query_text)
        return self.weaviate_service.query_document(document_id, query_embedding ,limit)