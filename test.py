#test.py
import requests
import json
import os

# Base URL of your Flask application (assuming it's running on localhost:5000)
BASE_URL = "http://127.0.0.1:5000"

# --- Helper Functions ---

def upload_file(file_path, metadata=None):
    """Uploads a file and returns the response and document ID."""
    url = f"{BASE_URL}/documents"
    files = {'file': open(file_path, 'rb'),'content_type':'application/pdf'}
    data = {}
    if metadata:
        data['metadata'] = json.dumps(metadata)  # Ensure metadata is a JSON string
    response = requests.post(url, files=files, data=data)
    files['file'].close()
    if response.status_code == 201:
        return response, response.json()['document_id']
    else:
        return response, None

def update_file(document_id, file_path, metadata=None):
    """Updates a file and returns the response."""
    url = f"{BASE_URL}/documents/{document_id}"
    files = {'file': open(file_path, 'rb')}
    data = {}
    if metadata:
        data['metadata'] = json.dumps(metadata)
    response = requests.put(url, files=files, data=data)
    files['file'].close()
    return response

def delete_file(document_id):
    """Deletes a file and returns the response."""
    url = f"{BASE_URL}/documents/{document_id}"
    response = requests.delete(url)
    return response

def query_document(document_id, query_text):
    """Queries a document and returns the response."""
    url = f"{BASE_URL}/queries/{document_id}?query={query_text}"
    response = requests.get(url)
    return response


# --- Test Functions (without pytest) ---

def create_test_files(test_dir="test_files"):
    """Creates test files for different formats."""
    os.makedirs(test_dir, exist_ok=True)

    # PDF file
    pdf_path = os.path.join(test_dir, "test.pdf")
    if not os.path.exists(pdf_path):
        with open(pdf_path, "w") as f:
            f.write("%PDF-1.7\nDummy PDF content")

    # DOCX file
    # docx_path = os.path.join(test_dir, "test.docx")
    # if not os.path.exists(docx_path):
    #     with open(docx_path, "w") as f:
    #         f.write("Dummy DOCX content")

    # # TXT file
    # txt_path = os.path.join(test_dir, "test.txt")
    # if not os.path.exists(txt_path):
    #     with open(txt_path, "w") as f:
    #         f.write("This is a test text file.")

    # # JSON file
    # json_path = os.path.join(test_dir, "test.json")
    # if not os.path.exists(json_path):
    #     with open(json_path, "w") as f:
    #         json.dump({"key1": "value1", "key2": 123}, f)

    return {
        "pdf": pdf_path,
        "docx": "docx_path",
        "txt": "txt_path",
        "json": "json_path",
    }


def test_upload_and_query_pdf(test_files):
    """Tests uploading and querying a PDF file."""
    print("\nTesting PDF Upload and Query...")
    file_path = test_files["pdf"]
    metadata = {"author": "Test Author", "tags": ["pdf", "test"]}
    print("hello")
    response, document_id = upload_file("test_files/test.pdf", metadata)
    print(f"  Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201: return  # Stop if upload fails
    
    query = "data science"
    response = query_document("3c6c6977-35e8-45c5-97fb-1cd7be128e04", query)
    print(f"  Query Response: {response.status_code}, {response.text}")
    
    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")



def test_upload_and_query_docx(test_files):
    """Tests uploading and querying a DOCX file."""
    print("\nTesting DOCX Upload and Query...")
    file_path = test_files["docx"]

    response, document_id = upload_file(file_path)
    print(f"  Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201: return

    query = "Dummy DOCX"
    response = query_document(document_id, query)
    print(f"  Query Response: {response.status_code}, {response.text}")

    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")


def test_upload_and_query_txt(test_files):
    """Tests uploading and querying a TXT file."""
    print("\nTesting TXT Upload and Query...")
    file_path = test_files["txt"]

    response, document_id = upload_file(file_path)
    print(f"  Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201: return

    query = "test text file"
    response = query_document(document_id, query)
    print(f"  Query Response: {response.status_code}, {response.text}")

    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")


def test_upload_and_query_json(test_files):
    """Tests uploading and querying a JSON file."""
    print("\nTesting JSON Upload and Query...")
    file_path = test_files["json"]

    response, document_id = upload_file(file_path)
    print(f"  Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201: return

    query = "value1"
    response = query_document(document_id, query)
    print(f"  Query Response: {response.status_code}, {response.text}")

    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")


def test_update_document(test_files):
    """Tests updating a document."""
    print("\nTesting Document Update...")
    file_path = test_files["txt"]

    response, document_id = upload_file(file_path)
    print(f"  Initial Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201: return

    updated_file_path = os.path.join(os.path.dirname(file_path), "updated_test.txt")
    with open(updated_file_path, "w") as f:
        f.write("This is the updated text file.")

    updated_metadata = {"author": "Updated Author"}
    response = update_file(document_id, updated_file_path, updated_metadata)
    print(f"  Update Response: {response.status_code}, {response.text}")

    original_query = "test text file"
    response = query_document(document_id, original_query)
    print(f"  Query (Original): {response.status_code}, {response.text}")

    query = "updated text file"
    response = query_document(document_id, query)
    print(f"  Query (Updated): {response.status_code}, {response.text}")

    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")
    os.remove(updated_file_path)


def test_delete_nonexistent_document():
    """Tests deleting a document that doesn't exist."""
    print("\nTesting Delete Nonexistent Document...")
    response = delete_file("nonexistent-id")
    print(f"  Delete Response: {response.status_code}, {response.text}")


def test_query_without_query_parameter(test_files):
  """Tests querying without providing query text"""
  print("\nTesting query without parameters...")
  file_path = test_files["txt"]
  response, document_id = upload_file(file_path)
  print(f"  Upload Response: {response.status_code}, {response.text}")
  if response.status_code != 201: return
  #query without query param.
  url = f"{BASE_URL}/queries/{document_id}"
  response = requests.get(url)
  print(f"  Query Response: {response.status_code}, {response.text}")
  # Delete
  response = delete_file(document_id)
  print(f"  Delete Response: {response.status_code}, {response.text}")


def test_upload_no_file():
    """Tests uploading without providing a file."""
    print("\nTesting Upload Without File...")
    url = f"{BASE_URL}/documents"
    response = requests.post(url)
    print(f"  Upload Response: {response.status_code}, {response.text}")

def test_upload_invalid_metadata():
    """Tests uploading with invalid metadata (not a JSON string)."""
    print("\nTesting Upload with Invalid Metadata...")
    url = f"{BASE_URL}/documents"
    files = {'file': open(test_files["txt"], 'rb')}
    data = {'metadata': 'invalid json'}  # Not a JSON string
    response = requests.post(url, files=files, data=data)
    files['file'].close()
    print(f"  Upload Response: {response.status_code}, {response.text}")


if __name__ == "__main__":
    test_files = create_test_files()

    test_upload_and_query_pdf(test_files)
    # test_upload_and_query_docx(test_files)
    # test_upload_and_query_txt(test_files)
    # test_upload_and_query_json(test_files)
    # test_update_document(test_files)
    # test_delete_nonexistent_document()
    # test_query_without_query_parameter(test_files)
    # test_upload_no_file()
    # test_upload_invalid_metadata()
    print("\nAll tests completed.")