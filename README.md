# Document Query System Readme

This project implements a document query system that allows users to upload, update, delete, and query documents using a vector database (Weaviate) for efficient similarity search. The system supports various file types (PDF, DOCX, TXT, JSON) and uses embeddings to represent documents and queries.

## System Architecture

The system is composed of the following key components:

1.  **Flask API:**  Provides RESTful endpoints for interacting with the system.  Handles document management (upload, update, delete) and querying.
2.  **Document Service:**  Manages the processing of documents. This includes:
    *   Reading and parsing files (using LlamaParse, MarkItDown, and standard file readers).
    *   Chunking documents into smaller, manageable pieces (using `langchain_text_splitters`, with specific strategies for PDF/DOCX, TXT and JSON).
    *   Interacting with the Embedding Service and Weaviate Service.
3.  **Embedding Service:**  Generates vector embeddings for text. It supports:
    *   **Google Gemini:**  Uses the `text-embedding-004` model (requires `GEMINI_API_KEY`). This is the **primary** embedding method used in the provided code.
    *   *(Commented out)*  **Sentence Transformers:**  A fallback option using Hugging Face models (defaults to `sentence-transformers/all-MiniLM-L6-v2`, configurable via `HUGGINGFACE_MODEL_NAME`).
4.  **Weaviate Service:**  Handles interactions with the Weaviate vector database.  This includes:
    *   Creating the `Document` collection with appropriate schema (properties for filename, content type, chunk content, sort key, original document ID, and metadata).
    *   Indexing document chunks with their embeddings.
    *   Performing vector-based queries (using `near_vector` from weaviate).
    *   Deleting documents (by original document ID).
5.  **File Utils:**  Provides utility functions for reading and parsing various file types, including handling potential parsing errors and content type detection. Used LLamaParse as primary parsing tool and added markitdown as a fallback mechanism.
6.  **Configuration (Config):**  Manages configuration settings, loading them from environment variables (using `python-dotenv`).
7.  **Models:**  Defines data classes (`Document`, `QueryResult`) for representing documents and query results.
8. **Upload Monitoring Script (`monitor_uploads.py`):** A script that watches a specified directory for new or modified files, automatically uploads or updates them, and moves them to a processed directory.  It uses `watchdog` for file system monitoring and maintains a JSON file (`processed_files.json`) to track processed files and their hashes to avoid redundant processing.

## Workflow

### Document Upload/Update

1.  **File Upload (via API or `monitor_uploads.py`):** A user uploads a file (PDF, DOCX, TXT, or JSON) through the `/documents` API endpoint (POST request with `action=upload`) or places it in the monitored upload directory.  The request includes the file, content type, and optional metadata (as JSON).  The `monitor_uploads.py` script automatically detects new or changed files.
2.  **File Handling:** The Flask app saves the uploaded file to a temporary directory (`data/temp` by default).
3.  **File Parsing:** The `DocumentService` uses `file_utils.read_and_parse_file` to read and parse the file based on its content type:
    *   **PDF/DOCX:**  Attempts to use LlamaParse first (requires `LLAMA_CLOUD_API_KEY`).  If LlamaParse fails, it falls back to MarkItDown.  The output is Markdown text.
    *   **TXT:**  Reads the file content directly.
    *   **JSON:** Loads the JSON data and converts it to a JSON string.
4.  **Chunking:**  The `DocumentService` chunks the parsed content into smaller segments:
    *   **PDF/DOCX:**  Uses `MarkdownHeaderTextSplitter` to split based on Markdown headers, then falls back to `RecursiveCharacterTextSplitter` for chunks exceeding the configured size (`CHUNK_SIZE`, default 1000).
    *   **TXT:** Uses `RecursiveCharacterTextSplitter` with a period (`.`) as the separator.
    * **JSON** No Chunking, file is sent as one large chunk.
5.  **Embedding Generation:**  The `EmbeddingService` generates embeddings for each chunk using the Google Gemini `text-embedding-004` model.
6.  **Indexing:** The `WeaviateService` indexes each chunk and its embedding in the `Document` collection.  It stores the filename, content type, chunk content, a sort key for chunk order, the original document ID, and metadata.
7.  **Update (if applicable):** If the `action` is `update`, the system first deletes all existing chunks associated with the provided `document_id` and then proceeds with the steps above to index the new content.
8. **File Movement (by `monitor_uploads.py`):** After successful processing, the file is moved from the `UPLOAD_FOLDER` to the `PROCESSED_FOLDER`.

### Document Query

1.  **Query Request:** A user sends a query request to the `/queries` API endpoint (POST request) with the `document_id` and the `query` text. Optionally a `num_chunks_return` can be supplied.
2.  **Embedding Generation:**  The `EmbeddingService` generates an embedding for the query text using Gemini.
3.  **Vector Search:**  The `WeaviateService` performs a vector search (`near_vector`) in the `Document` collection using the query embedding.  It filters results by the provided `document_id` to retrieve only chunks from the relevant document.
4.  **Result Retrieval:**  The `WeaviateService` retrieves the most similar chunks (up to a limit, default 6). It returns the chunk content, similarity score (calculated from the distance), and metadata.
5.  **Response:**  The API returns a JSON response containing an array of `QueryResult` objects, each with the `document_id`, `snippet`, `score`, and `metadata`, and `chunk_order_key`.

### Document Deletion

1.  **Deletion Request:** A user sends a deletion request to the `/documents` API endpoint (POST request with `action=delete` and the `document_id`).
2.  **Deletion:** The `WeaviateService` deletes all chunks associated with the specified `document_id` from the `Document` collection.

## API Documentation

### `/documents` (POST)

This endpoint handles document upload, update, and deletion. It uses a single POST endpoint with an `action` parameter to differentiate between operations.

**Request Parameters (Form Data):**

*   `action`:  Required.  Specifies the operation to perform:
    *   `"upload"`:  Uploads a new document.
    *   `"update"`:  Updates an existing document.  Requires `document_id`.
    *   `"delete"`:  Deletes a document.  Requires `document_id`.
*   `file`:  Required for `upload` and `update`.  The file to be uploaded or updated.
*   `content_type`:  Required for `upload` and `update`.  The MIME type of the file.  Supported types:
    *   `"application/pdf"`
    *   `"application/vnd.openxmlformats-officedocument.wordprocessingml.document"`
    *   `"text/plain"`
    *    `"application/json"`
*   `metadata`:  Optional for `upload` and `update`.  A JSON string representing additional metadata to be associated with the document.
*   `document_id`:  Required for `update` and `delete`. The ID of the document to update or delete.

**Responses:**

*   **Upload:**
    *   `201 Created`:  Success.  Returns a JSON object with a `message` and the `document_id` of the newly created document.
    *   `400 Bad Request`:  Missing file, invalid content type, or invalid metadata.
    *   `500 Internal Server Error`:  Error during processing.
*   **Update:**
    *   `200 OK`: Success. Returns a JSON object with a `message` and the `document_id`.
    *   `400 Bad Request`:  Missing `document_id`, missing file, invalid content type, or invalid metadata.
    *   `500 Internal Server Error`:  Error during processing.
*   **Delete:**
    *   `200 OK`: Success. Returns a JSON object with a `message` indicating the document was deleted.
    *   `400 Bad Request`:  Missing `document_id`.
    *   `500 Internal Server Error`:  Error during deletion.
* **Invalid Action:**
    *  `400 Bad Request`: Returns a JSON object with a `message` indicating action is invalid.

### `/queries` (POST)

This endpoint handles document queries.

**Request Body (JSON):**

*   `document_id`:  Required.  The ID of the document to query.
*   `query`:  Required.  The query text.
*   `num_chunks_return` : Optional. The number of chunks to return .

**Responses:**

*   `200 OK`:  Success.  Returns a JSON array of `QueryResult` objects.  Each object has the following fields:
    *   `document_id`: The ID of the document.
    *   `snippet`:  The text of the matching chunk.
    *   `score`:  The similarity score (1 - distance) between the query and the chunk.
    *   `metadata`:  The metadata associated with the chunk.
    *   `chunk_order_key`: The order of the chunk.
*   `400 Bad Request`:  Missing `document_id` or `query`.
*   `500 Internal Server Error`:  Error during query processing.



## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Linux/macOS
    .venv\Scripts\activate  # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set environment variables:**

    Create a `.env` file in the project root directory and set the following variables (refer to `.env.example`):

    ```
    GEMINI_API_KEY="Your Gemini API key"
    WEAVIATE_URL="Your Weaviate instance URL"
    WEAVIATE_API_KEY="Your Weaviate API key"  # If required by your Weaviate instance
    LLAMA_CLOUD_API_KEY="Your LlamaParse API Key"
    # Optional:
    HUGGINGFACE_MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"  # If you want to use a different HF model
    FLASK_RUN_HOST="0.0.0.0"
    FLASK_RUN_PORT=5000
    FLASK_DEBUG="True"  # Set to "False" in production
    ```

5.  **Run the Flask application:**

    ```bash
    python app.py
    ```
    This will start the Flask development server.  The API will be accessible at `http://0.0.0.0:5000` (or the host/port you configured).

6.  **Run the upload monitoring script (optional):**

    In a separate terminal, run:

    ```bash
    python scripts/monitor_uploads.py
    ```
    This script will monitor the `data/uploads` directory and automatically process any new or modified files.

## API Usage with `curl`

This section provides examples of how to interact with the API using the `curl` command-line tool. Pay close attention to file paths and your current working directory.

### Important Notes:

- **Current Working Directory:** When using `curl` with `@` to upload files, the path to the file is *relative to your current working directory*. Make sure you are in the correct directory or use absolute paths for the files. I'll show examples of both.
- **Windows vs. Linux/macOS:** File paths use backslashes (`\`) on Windows and forward slashes (`/`) on Linux/macOS. The examples below use forward slashes, consistent with the rest of your project (and generally preferred even on Windows for cross-platform compatibility). Adapt as needed.
- **JSON Formatting:** When sending JSON data, ensure it's properly formatted. You can use online JSON validators to check. Use `-H "Content-Type: application/json"` for JSON requests.
- **`localhost` vs. `127.0.0.1`:** These are generally interchangeable. I'll use `127.0.0.1` to match your `monitor_uploads.py` script.
- **Quotes:** For string values with spaces, use quotes.

---

### 1. Upload a Document (`action=upload`)

**Scenario:** You have a file named `my_document.pdf` in a directory `documents` which is in the same directory as your `app.py` file.

#### Method 1: Relative Path (assuming you're in the project root)

```bash
curl -X POST -F "action=upload" -F "file=@documents/my_document.pdf" -F "content_type=application/pdf" -F 'metadata={"author": "John Doe", "date": "2024-10-27"}' https://ringg-assignment.onrender.com/documents
```

#### Method 2: Absolute Path (works from anywhere)

```bash
curl -X POST -F "action=upload" -F "file=@/path/to/your/project/documents/my_document.pdf" -F "content_type=application/pdf" -F 'metadata={"author": "John Doe", "date": "2024-10-27"}' https://ringg-assignment.onrender.com/documents
```

### Explanation:

- `-X POST`: Specifies the HTTP method (POST).
- `-F`: Specifies form data (used for file uploads and other parameters).
- `file=@documents/my_document.pdf`: Uploads the file. `@` tells `curl` to read the file. The path is relative to your current working directory.
- `content_type=application/pdf`: Sets the content type. Change this as needed (e.g., `text/plain`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/json`).
- `metadata={"author":...}`: Sends optional metadata as a JSON string.
- `http://127.0.0.1:5000/documents`: The API endpoint.

#### Example with a Text File (`my_document.txt`) and You're in a Different Directory:

Let's say you're in your home directory (`~`) and the project is in `~/projects/my_project`.

```bash
# From your home directory (~):
curl -X POST -F "action=upload" -F "file=@projects/my_project/documents/my_document.txt" -F "content_type=text/plain" https://ringg-assignment.onrender.com/documents
```

---

### 2. Update a Document (`action=update`)

**Scenario:** You want to update the document with `document_id="123-abc"` with a new file `updated_document.docx`.

```bash
curl -X POST -F "action=update" -F "document_id=123-abc" -F "file=@documents/updated_document.docx" -F "content_type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" https://ringg-assignment.onrender.com/documents
```

- `document_id=123-abc`: The ID of the document to update. This is crucial for updates.

---

### 3. Delete a Document (`action=delete`)

**Scenario:** You want to delete the document with `document_id="123-abc"`.

```bash
curl -X POST -F "action=delete" -F "document_id=123-abc" https://ringg-assignment.onrender.com/documents
```

---

### 4. Query a Document

**Scenario:** You want to query the document with `document_id="123-abc"` for the text "search term". You want 3 chunks returned.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"document_id": "123-abc", "query": "search term", "num_chunks_return": 3}' https://ringg-assignment.onrender.com/queries
```

- `-H "Content-Type: application/json"`: Indicates that you're sending JSON data.
- `-d '{"document_id": "123-abc", "query": "search term"}'`: Sends the query parameters as a JSON object. This is different from file uploads.

#### Example Query with Spaces in the Search Term:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"document_id": "123-abc", "query": "my search term with spaces"}' https://ringg-assignment.onrender.com/queries
```

#### Example to Get Results for All Documents:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"document_id": "", "query": "search term"}' https://ringg-assignment.onrender.com/queries
```

---

### 5. Uploading a JSON File

```bash
curl -X POST -F "action=upload" -F "file=@data/my_data.json" -F "content_type=application/json" https://ringg-assignment.onrender.com/documents
```

Make sure `data/my_data.json` is a valid JSON file.

---

These examples cover the main API interactions and demonstrate how to handle file paths correctly. Remember to adjust the paths, document IDs, content types, and query text to match your specific needs. Always double-check your current working directory when using relative paths.


## Improvements and TODOs

*   **Error Handling:** Improve error handling throughout the application, especially in API endpoints and the `monitor_uploads.py` script. Provide more informative error messages to the user.
*   **JSON Chunking:** Tried to implement more sophisticated chunking for JSON files, potentially using a recursive approach and tracking hierarchy.  Currently it treats the whole JSON as a single chunk.Also I was confused about how the input json and queries would look like in the case of query and upload and what the objective was .


