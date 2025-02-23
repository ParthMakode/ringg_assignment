# ./scripts/monitor_uploads.py
import time
import os
import hashlib
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import uuid  # Import the uuid module


BASE_URL = "http://127.0.0.1:5000"  # Or your deployed URL
UPLOAD_FOLDER = "data/uploads"
PROCESSED_FOLDER = "data/processed"
METADATA_FILE = os.path.join(PROCESSED_FOLDER, "processed_files.json")

def calculate_hash(file_path):
    """Calculates the SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(4096)  # Read in 4KB chunks
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def load_processed_files():
    """Loads the metadata of processed files from the JSON file."""
    try:
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_processed_files(processed_files):
    """Saves the metadata of processed files to the JSON file."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(processed_files, f, indent=4)

def upload_file(file_path, content_type, metadata=None, document_id=None, action="upload"):
    """Uploads or updates a file using the /documents endpoint."""
    url = f"{BASE_URL}/documents"
    files = {'file': open(file_path, 'rb')}
    data = {
        'action': action,
        'content_type': content_type,
    }
    if metadata:
        data['metadata'] = json.dumps(metadata)
    if document_id:
        data['document_id'] = document_id

    response = requests.post(url, files=files, data=data)
    files['file'].close()
    return response

def get_content_type(file_path):
    """Determines the content type based on the file extension."""
    _, ext = os.path.splitext(file_path)
    if ext == ".pdf":
        return "application/pdf"
    elif ext == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext == ".txt":
        return "text/plain"
    elif ext == ".json":
        return "application/json"
    else:
        return "application/octet-stream"  # Default fallback


class MyEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.startswith(UPLOAD_FOLDER):
            self.process_file(event.src_path)


    def process_file(self, file_path):
        """Processes a new file in the upload folder."""
        if not os.path.exists(file_path):
            print(f"File disappeared before processing: {file_path}")
            return
        time.sleep(1)
        print(f"New file detected: {file_path}")
        file_hash = calculate_hash(file_path)
        file_name = os.path.basename(file_path)
        content_type = get_content_type(file_path)

        processed_files = load_processed_files()
        existing_entry = next((entry for entry in processed_files if entry["filename"] == file_name), None)

        if existing_entry and existing_entry["hash"] == file_hash:
            print(f"File {file_name} already processed (same hash). Skipping.")
            return

        document_id = None
        action = "upload"

        if existing_entry:  # File with same name exists
            if existing_entry["hash"] != file_hash: #different content.
                print(f"File {file_name} updated (different hash). Updating.")
                document_id = existing_entry["document_id"]
                action = "update"  #Crucial:  Use the "update" action
            else:  # same content
                print("skipping")
                return

        # if not document_id:  # Remove: Don't generate UUID here
        #     document_id=str(uuid.uuid4())
        response = upload_file(file_path, content_type, document_id=document_id, action=action)

        if response.status_code in (200, 201): #check for the action
            print(f"File {file_name} processed successfully. Response: {response.status_code}")
            # Get document_id from response
            try:
                response_data = response.json()
                returned_document_id = response_data.get('document_id')
                if not returned_document_id:
                    print("Error: document_id not found in response.")
                    return  # Or handle the error appropriately
            except json.JSONDecodeError:
                print("Error: Could not decode response as JSON.")
                return

            #Update metadata
            if existing_entry:
                existing_entry["hash"] = file_hash
                existing_entry["document_id"] = returned_document_id  # Use returned ID
            else:
                processed_files.append({"filename": file_name, "hash": file_hash, "document_id": returned_document_id})  # Use returned ID
            save_processed_files(processed_files)

            # Move to processed folder
            new_file_path = os.path.join(PROCESSED_FOLDER, file_name)
            os.makedirs(PROCESSED_FOLDER,exist_ok=True)
            os.rename(file_path, new_file_path)
            print(f"File moved to {new_file_path}")
        else:
            print(f"Error processing file {file_name}. Status: {response.status_code}, Response: {response.text}")

def main():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)  # Ensure processed folder exists

    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, UPLOAD_FOLDER, recursive=False)
    observer.start()
    print(f"Monitoring {UPLOAD_FOLDER} for new files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()