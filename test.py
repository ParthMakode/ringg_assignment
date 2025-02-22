import requests
import json
import os
import time

# Base URL of your Flask application
BASE_URL = "http://127.0.0.1:5000"

# --- Helper Functions ---

def upload_file(file_path, content_type, metadata=None):
    """Uploads a file using the unified /documents endpoint."""
    url = f"{BASE_URL}/documents"
    files = {'file': open(file_path, 'rb')}
    data = {
        'action': 'upload',
        'content_type': content_type
    }
    if metadata:
        data['metadata'] = json.dumps(metadata)
    response = requests.post(url, files=files, data=data)
    files['file'].close()
    if response.status_code == 201:
        return response, response.json()['document_id']
    return response, None

def update_file(document_id, file_path, content_type, metadata=None):
    """Updates a file using the unified /documents endpoint."""
    url = f"{BASE_URL}/documents"
    files = {'file': open(file_path, 'rb')}
    data = {
        'action': 'update',
        'document_id': document_id,
        'content_type': content_type
    }
    if metadata:
        data['metadata'] = json.dumps(metadata)
    response = requests.post(url, files=files, data=data)  # Use POST
    files['file'].close()
    return response

def delete_file(document_id):
    """Deletes a file using the unified /documents endpoint."""
    url = f"{BASE_URL}/documents"
    data = {
        'action': 'delete',
        'document_id': document_id
    }
    response = requests.post(url, data=data)  # Use POST
    return response

def query_document(document_id, query_text):
    """Queries a document using the /queries endpoint."""
    url = f"{BASE_URL}/queries"
    data = {
        'document_id': document_id,
        'query': query_text
    }
    # Send as JSON in the request body
    response = requests.post(url, json=data)
    return response


# --- Test Functions ---

def create_test_files(test_dir="test_files"):
    """Creates test files for different formats."""
    os.makedirs(test_dir, exist_ok=True)

    # PDF file
    pdf_path = os.path.join(test_dir, "original_test.pdf")
    # if not os.path.exists(pdf_path):
    #     with open(pdf_path, "w") as f:
    #         f.write("%PDF-1.7\nDummy PDF content")  # Minimal PDF

    # # DOCX file
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
        "txt": "txt_path,",
        "json": "json_path",
    }


def test_upload_and_query_pdf(test_files):
    """Tests uploading and querying a PDF file."""
    print("\nTesting PDF Upload and Query...")
    file_path = test_files["pdf"]
    metadata = {"author": "Test Author", "tags": ["pdf", "test"]}
    content_type = "application/pdf"

    response, document_id = upload_file(file_path, content_type, metadata)
    print(f"  Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201:
        return  # Stop if upload fails

    query = "disqualifications"
    response = query_document(document_id, query)
    print(f"  Query Response: {response.status_code}, {response.text}")

    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")


def test_upload_and_query_docx(test_files):
    """Tests uploading and querying a DOCX file."""
    print("\nTesting DOCX Upload and Query...")
    file_path = test_files["docx"]
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    response, document_id = upload_file(file_path, content_type)
    print(f"  Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201:
        return

    query = "Dummy DOCX"
    response = query_document(document_id, query)
    print(f"  Query Response: {response.status_code}, {response.text}")

    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")


def test_upload_and_query_txt(test_files):
    """Tests uploading and querying a TXT file."""
    print("\nTesting TXT Upload and Query...")
    file_path = test_files["txt"]
    content_type = "text/plain"

    response, document_id = upload_file(file_path, content_type)
    print(f"  Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201:
        return

    query = "test text file"
    response = query_document(document_id, query)
    print(f"  Query Response: {response.status_code}, {response.text}")

    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")


def test_upload_and_query_json(test_files):
    """Tests uploading and querying a JSON file."""
    print("\nTesting JSON Upload and Query...")
    file_path = test_files["json"]
    content_type = "application/json"

    response, document_id = upload_file(file_path, content_type)
    print(f"  Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201:
        return

    query = "value1"
    response = query_document(document_id, query)
    print(f"  Query Response: {response.status_code}, {response.text}")

    response = delete_file(document_id)
    print(f"  Delete Response: {response.status_code}, {response.text}")


def test_update_document(test_files):
    """Tests updating a document."""
    print("\nTesting Document Update...")
    file_path = test_files["txt"]
    content_type = "text/plain"

    response, document_id = upload_file(file_path, content_type)
    print(f"  Initial Upload Response: {response.status_code}, {response.text}")
    if response.status_code != 201:
        return

    updated_file_path = os.path.join(os.path.dirname(file_path), "updated_test.txt")
    with open(updated_file_path, "w") as f:
        f.write("This is the updated text file.")

    updated_metadata = {"author": "Updated Author"}
    response = update_file(document_id, updated_file_path, content_type, updated_metadata) # Pass content_type
    print(f"  Update Response: {response.status_code}, {response.text}")

    # original_query = "test text file"
    # response = query_document(document_id, original_query)
    # print(f"  Query (Original): {response.status_code}, {response.text}")

    query = "updated text file"
    response = query_document(document_id, query)
    print(f"  Query (Updated): {response.status_code}, {response.text}")

    # response = delete_file(document_id)
    # print(f"  Delete Response: {response.status_code}, {response.text}")
    # os.remove(updated_file_path)  # Clean up the updated file





if __name__ == "__main__":
    test_files = create_test_files()

    test_upload_and_query_pdf(test_files)
    # test_upload_and_query_docx(test_files)
    # test_upload_and_query_txt(test_files)
    # test_upload_and_query_json(test_files)
    # test_update_document(test_files)
    
    print("\nAll tests completed.")