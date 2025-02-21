from dataclasses import dataclass

@dataclass
class Document:
    id: str  # Weaviate ID or your own ID
    filename: str
    content: str  # Or a path to the content, depending on storage strategy
    content_type: str # "application/pdf", "text/plain", etc.
    metadata: dict  # Any additional metadata

@dataclass
class QueryResult:
    document_id: str
    snippet: str
    score: float # Similarity score from Weaviate
    metadata: dict
    chunk_order_key:int