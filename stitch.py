import os

def collect_code_with_paths(directory, extensions=None):
    if extensions is None:
        extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.h', '.cs', '.rb', '.go', '.txt', '.env.example'}
    
    stitched_code = []
    
    for root, _, files in os.walk(directory):
        if ".venv" in root.split(os.sep):
            continue
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    stitched_code.append(f"### FILE: {file_path}\n{content}\n")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return "\n".join(stitched_code)

if __name__ == "__main__":
    directory = input("Enter the directory path: ")
    result = collect_code_with_paths(directory)
    
    with open("stitched_code.txt", "w", encoding="utf-8") as output_file:
        output_file.write(result)
    
    print("Stitched code saved to 'stitched_code.txt'")
