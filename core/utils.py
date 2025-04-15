class Utils:
    
    def __init__(self):
        pass
    
    def readFiles(self, file_path):
        content = ""
        try:
            with open(file_path, "r") as file:
                content = file.read()
        except FileNotFoundError:
            print(f"The file {file_path} cannot be found")
        
        return content