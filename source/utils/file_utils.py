import json
import os  # Import the 'os' module
from typing import Optional
from markitdown import MarkItDown  # Assuming you have this installed
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader
from dotenv import load_dotenv
load_dotenv()

def read_and_parse_file(file_path: str, content_type: Optional[str] = None) -> str:
    """Reads and parses a file with fallback parsing and content type validation."""

    # 1. Validate/Determine Content Type
    valid_content_types = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/json": ".json",
        "text/plain": ".txt",
    }

    if content_type:
        if content_type not in valid_content_types:
            raise ValueError(f"Invalid content_type provided: {content_type}")
    else:
        # Infer from file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        reverse_lookup = {v: k for k, v in valid_content_types.items()}
        content_type = reverse_lookup.get(ext)
        if not content_type:
            raise ValueError(f"Could not determine content type for file: {file_path}")

    # 2. Parsing Logic (with Fallback)
    try:
        if content_type in ("application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
            try:
                # Primary: LlamaParse
                parser = LlamaParse(result_type="markdown")
                file_extractor = {".pdf": parser, ".docx": parser}
                documents = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor).load_data()
                return "\n".join([doc.text for doc in documents]) #access text directly.

            except Exception as e:
                print(f"LlamaParse failed: {e}. Attempting fallback...")
                try:
                    md = MarkItDown()
                    result = md.convert(file_path)
                    return result.text_content
                except Exception as fallback_e:
                    raise Exception(f"Fallback parsing also failed: {fallback_e}")
                # raise Exception("Fallback not installed; LlamaParse Failed.") # Remove when you install MarkItDown

        elif content_type == "application/json":
            with open(file_path, "r") as file:
                data = json.load(file)
                return json.dumps(data)  # Return as a JSON string

        elif content_type == "text/plain":
            with open(file_path, "r") as file:
                return file.read()

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error during file processing: {e}")