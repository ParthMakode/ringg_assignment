import weaviate
from weaviate import WeaviateClient
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter,MetadataQuery

from weaviate.classes.init import Auth# from weaviate.classes.init import Auth

from typing import List, Dict, Any
from source.models import Document, QueryResult  # Assuming these are defined
from source.utils.config import Config  # Assuming this is defined

class WeaviateService:
    def __init__(self, config: Config):
        self.class_name = "Document"  
        self.client = self._init_client(config)
        self._create_collection()  

    def _init_client(self, config: Config) -> WeaviateClient:
        """Initializes the Weaviate client with appropriate authentication."""

        if config.WEAVIATE_URL:
            # Connect to a remote Weaviate instance
            if config.WEAVIATE_API_KEY:
                auth_cred = Auth.api_key(config.WEAVIATE_API_KEY)
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=config.WEAVIATE_URL,
                auth_credentials=auth_cred,
            )

        return client

    def _create_collection(self):
        """Creates the Weaviate collection if it doesn't exist."""
        if not self.client.collections.exists(self.class_name):
            self.client.collections.create(
                name=self.class_name,
                properties=[
                    Property(
                        name="filename", data_type=DataType.TEXT
                    ),
                    Property(
                        name="content_type", data_type=DataType.TEXT
                    ),
                    Property(
                        name="content_chunk", data_type=DataType.TEXT
                    ),
                    Property(
                        name="chunk_sort_key", data_type=DataType.INT
                    ),
                    Property(
                        name="original_document_id", data_type=DataType.TEXT
                    ),
                    Property(
                        name="metadata", data_type=DataType.TEXT
                    ),
                ],
                vectorizer_config=[Configure.NamedVectors.none(
                    name="chunk_vectors",
                    vector_index_config=Configure.VectorIndex.hnsw() 
                )]
            )
            
    def index_document(self, document: Document, embeddings: List[List[float]]) -> str:
        """Index document chunks with their embeddings"""
        collection = self.client.collections.get(self.class_name)
        try:
            for i, embedding in enumerate(embeddings):
                print(i)
                print(embedding[0:5])
                collection.data.insert(
                    properties={
                        "filename": document.filename,
                        "content_type": document.content_type,
                        "content_chunk": document.content[i],
                        "original_document_id": document.id,
                        "chunk_sort_key": i,
                        "metadata": str(document.metadata),
                    },
                    vector=embedding,
                )
        except Exception as e:
            print(e)

        return document.id
    # def index_json_document(self, document: Document, chunks,hierarchy_paths, embeddings: List[List[float]]) -> str:
    #     """
    #     Process a JSON document using hierarchical chunking.
    #     The method updates the document's content and metadata (storing hierarchy paths)
    #     then indexes the document chunks using the provided embeddings.
    #     """
    #     chunks, hierarchy_paths 
    #     document.content = chunks
    #     # Extend or initialize metadata to include hierarchical paths.
    #     if document.metadata is None:
    #         document.metadata = {}
    #     document.metadata["hierarchy_paths"] = hierarchy_paths
    #     return self.index_document(document, embeddings)
    def query_document(self, document_id: str, query_embedding: List[float], limit: int = 6) -> List[QueryResult]:
        """Query document chunks using vector search"""
        collection = self.client.collections.get(self.class_name)
        print("got collection")
        response=[]
        if(document_id != ""):
            response = collection.query.near_vector(
                near_vector=query_embedding,
                return_metadata=MetadataQuery(distance=True,score=True),
                limit=limit,
                # certainty=0.5,
                filters=Filter.by_property("original_document_id").equal(document_id),
                return_properties=["filename", "content_chunk", "chunk_sort_key", "original_document_id"]
            )
        else:
            response = collection.query.near_vector(
                near_vector=query_embedding,
                return_metadata=MetadataQuery(distance=True,score=True),
                limit=limit,
                # certainty=0.5,
                # filters=Filter.by_property("original_document_id").equal(document_id),
                return_properties=["filename", "content_chunk", "chunk_sort_key", "original_document_id"]
            )
        # print(response)
        results = []
        for obj in response.objects:
            results.append(QueryResult(
                document_id=obj.properties["original_document_id"],
                snippet=obj.properties["content_chunk"],
                score=1-obj.metadata.distance       , 
                # Convert distance to similarity score
                metadata=obj.metadata,
                chunk_order_key=obj.properties["chunk_sort_key"]
            ))
        print(len(results))
        return results
    # def query_hierarchical_json(self, document_id: str, query_embedding: List[float],
    #                             hierarchy_filter: str = None, limit: int = 6) -> List[QueryResult]:
    #     """
    #     Query JSON document chunks with optional hierarchical filtering.
    #     If a hierarchy_filter is provided, it will further restrict the search
    #     to chunks whose metadata (containing the hierarchy paths) includes the filter text.
    #     """
    #     collection = self.client.collections.get(self.class_name)
    #     # Build filter: first, ensure we only search within the document.
    #     filter_obj = Filter.by_property("original_document_id").equal(document_id)
    #     # If a hierarchy filter is specified, add an extra condition on the metadata.
    #     if hierarchy_filter:
    #         # Assumes that the 'metadata' field (stored as string) includes the hierarchy paths.
    #         filter_obj = filter_obj.and_(Filter.by_property("metadata").contains(hierarchy_filter))
    #     response = collection.query.near_vector(
    #         near_vector=query_embedding,
    #         return_metadata=MetadataQuery(distance=True, score=True),
    #         limit=limit,
    #         filters=filter_obj,
    #         return_properties=["filename", "content_chunk", "chunk_sort_key", "original_document_id"]
    #     )
    #     results = []
    #     for obj in response.objects:
    #         results.append(QueryResult(
    #             document_id=obj.properties["original_document_id"],
    #             snippet=obj.properties["content_chunk"],
    #             score=1 - obj.metadata.distance,
    #             metadata=obj.metadata,
    #             chunk_order_key=obj.properties["chunk_sort_key"]
    #         ))
    #     return results
    def delete_document(self, document_id: str):
        """Delete all chunks associated with a document"""
        collection = self.client.collections.get(self.class_name)
        collection.data.delete_many(
            where=Filter.by_property("original_document_id").equal(document_id)
        )
        return document_id
    
    def close(self):
        """Close the client connection"""
        self.client.close()

# def main():
#     service= WeaviateService(config=Config)


# main()
