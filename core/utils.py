from core.logger import logger

class Utils:
    
    def __init__(self):
        pass
    
    def readFiles(self, file_path):
        content = ""
        try:
            with open(file_path, "r") as file:
                content = file.read()
        except FileNotFoundError:
            error_msg = f"The file {file_path} cannot be found"
            logger.log_error(FileNotFoundError(error_msg), f"Attempted to read: {file_path}")
            print(error_msg)
        except Exception as e:
            logger.log_error(e, f"Error reading file: {file_path}")
            print(f"Error reading file {file_path}: {e}")
        
        return content