# from markitdown import MarkItDown
import json
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader
# from .config import Config
from dotenv import load_dotenv
load_dotenv()
# set up parser


print()
def read_and_parse_file(file_path: str, content_type: str) -> str:
    """Reads and parses a file based on its content type."""
    parser = LlamaParse(
    result_type="markdown")

# use SimpleDirectoryReader to parse our file
    file_extractor = {".pdf": parser,".docx":parser}
    # md = MarkItDown()
    try:
        if content_type == "application/pdf":
            print("got pdf")
            print("reading ",file_path)
            # result = md.convert(file_path)
            # print("document ",result.text_content)
            documents = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor).load_data()
            
            # return result.text_content
            return documents[0].text_resource.text
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            pass
            # result =md.convert(file_path)
            # print(result.text_content)
            documents = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor).load_data()
            
            # return result.text_content
            return documents[0].text_resource.text
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