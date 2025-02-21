from markitdown import MarkItDown
import json

def read_and_parse_file(file_path: str, content_type: str) -> str:
    """Reads and parses a file based on its content type."""
    md = MarkItDown()
    try:
        if content_type == "application/pdf":
            print("got pdf")
            result = md.convert(file_path)
            # print("document ",result.text_content)
        
            return result.text_content
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            result =md.convert(file_path)
            print(result.text_content)
            return result.text_content
        elif content_type == "application/json":
            with open(file_path, "r") as file:
                data = json.load(file)
                return json.dumps(data)  # Return as a JSON string
        elif content_type == "text/plain":
            with open(file_path, "r") as file:
                return file.read()
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error during file processing: {e}")