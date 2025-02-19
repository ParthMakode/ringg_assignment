import weaviate
import weaviate.classes as wvc
from weaviate import WeaviateClient
from weaviate.auth import AuthApiKey
from typing import List, Dict, Any
from source.models import Document, QueryResult  # Assuming these are defined
from source.utils.config import Config  # Assuming this is defined


class WeaviateService:
    def __init__(self, config: Config):
        self.class_name = "Document"  # Define the Weaviate class name
        self.client = self._init_client(config)
        self._create_schema()


    def _init_client(self, config: Config) -> WeaviateClient:
        """Initializes the Weaviate client with appropriate authentication."""

        if config.WEAVIATE_URL:
            # Connect to a remote Weaviate instance
            auth_config = None
            if config.WEAVIATE_API_KEY:
                auth_config = AuthApiKey(api_key=config.WEAVIATE_API_KEY)
            client = weaviate.Client(
                url=config.WEAVIATE_URL,
                auth_client_secret=auth_config
            )
        else:
          # Use embedded Weaviate (great for local development/testing)
          client = weaviate.Client(
                embedded_options=weaviate.embedded.EmbeddedOptions()
            )
        return client
    

    def _create_schema(self):
        """Creates the Weaviate schema if it doesn't exist."""
        if not self.client.schema.exists(self.class_name):
            class_obj = wvc.ConfigFactory.classes.rest(
                name=self.class_name,
                properties=[
                    wvc.Property(name="filename", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="content_type", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="content", data_type=wvc.DataType.TEXT),  # Store chunk text here
                    wvc.Property(name="original_document_id", data_type=wvc.DataType.TEXT),  # if chunking
                    wvc.Property(name="metadata", data_type=wvc.DataType.TEXT),  # Store as JSON string
                ],
                vectorizer=wvc.Vectorizer.NONE,  # We'll manage embeddings ourselves
            )
            self.client.schema.create_class(class_obj)
            
    def index_document(self, document: Document, embeddings: List[List[float]]) -> str:
      """Indexes document chunks and their embeddings using Weaviate's batch import."""
      with self.client.batch as batch:
          batch.configure(
            batch_size=100,
            # dynamic=True  # Enable dynamic batch sizing.  Good for most cases.
          )
          for i, embedding in enumerate(embeddings):
              data_object = {
                  "filename": document.filename,
                  "content_type": document.content_type,
                  # Handle both full document and chunked content
                  "content": document.content if len(embeddings) == 1 else document.content[i],
                  "original_document_id": document.id,
                  "metadata": str(document.metadata),  # Convert to JSON string
              }
              batch.add_data_object(
                  data_object=data_object,
                  class_name=self.class_name,
                  vector=embedding,
              )
      return document.id


    def query_document(self, document_id: str, query_embedding: List[float], limit: int = 5) -> List[QueryResult]:
        """Queries Weaviate for relevant chunks using nearVector search and a where filter."""

        # Use the new query API for better performance and readability
        response = (
            self.client.query
            .get(self.class_name, ["filename", "content", "content_type", "metadata", "original_document_id"])
            .with_near_vector({"vector": query_embedding})
            .with_limit(limit)
            .with_where({  # Filter by original_document_id
                "path": ["original_document_id"],
                "operator": "Equal",
                "valueText": document_id
            })
            .do()
        )
        
        results = []
        # Check for errors and handle the response
        if response and response.get('data') and response['data'].get('Get') and response['data']['Get'].get(self.class_name):
          for item in response['data']['Get'][self.class_name]:
                metadata = eval(item.get('metadata', '{}')) #parse metadata back to dictionary.
                results.append(QueryResult(
                    document_id=item.get('original_document_id', ''),
                    snippet=item.get('content', ''),
                    score=item.get('_additional', {}).get('certainty', 0.0), # Or 'distance'
                    metadata=metadata
                ))
          return results
        else: #handle errors.
          print(f"Error querying Weaviate: {response}")
          return []  # Or raise an exception, depending on your error handling strategy


    def delete_document(self, document_id: str):
        """Deletes all objects associated with a document ID."""
        where_filter = {
                "path": ["original_document_id"],
                "operator": "Equal",
                "valueText": document_id,
            }

        self.client.batch.delete_objects(
          class_name=self.class_name,
          where=where_filter
        )