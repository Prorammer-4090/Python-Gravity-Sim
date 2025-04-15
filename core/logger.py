import os
import traceback
import datetime
import inspect

class Logger:
    """
    Utility class for logging errors and messages to files in a log directory.
    """
    
    def __init__(self, log_dir="logs"):
        """
        Initialize the logger with a specified log directory.
        
        Args:
            log_dir (str): Directory where log files will be stored
        """
        self.log_dir = log_dir
        self._ensure_log_dir_exists()
        
    def _ensure_log_dir_exists(self):
        """Create the log directory if it doesn't exist."""
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
                print(f"Created log directory: {self.log_dir}")
            except Exception as e:
                print(f"Failed to create log directory: {e}")
    
    def _get_log_filename(self, prefix="error"):
        """Generate a timestamped log filename."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.log"
    
    def _get_caller_info(self):
        """Get information about the calling function/class."""
        stack = inspect.stack()
        # Look for the first frame that isn't in this file
        for frame in stack[1:]:
            if frame.filename != __file__:
                frame_info = frame
                break
        else:
            frame_info = stack[1]  # Default to first caller if nothing else found
            
        module = inspect.getmodule(frame_info[0])
        module_name = module.__name__ if module else "unknown_module"
        function_name = frame_info.function
        line_number = frame_info.lineno
        
        return f"{module_name}.{function_name}:{line_number}"
    
    def log_error(self, error, context=None):
        """
        Log an error to a file with traceback information.
        
        Args:
            error (Exception): The exception to log
            context (str, optional): Additional context information
        
        Returns:
            str: Path to the created log file
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        caller_info = self._get_caller_info()
        log_path = os.path.join(self.log_dir, self._get_log_filename())
        
        try:
            with open(log_path, 'w') as log_file:
                log_file.write(f"=== Error Log: {timestamp} ===\n\n")
                log_file.write(f"Location: {caller_info}\n")
                if context:
                    log_file.write(f"Context: {context}\n")
                log_file.write(f"Error Type: {type(error).__name__}\n")
                log_file.write(f"Error Message: {str(error)}\n\n")
                log_file.write("Traceback:\n")
                log_file.write(traceback.format_exc())
                
            print(f"Error logged to: {log_path}")
            return log_path
        except Exception as e:
            print(f"Failed to write error log: {e}")
            return None
    
    def log_message(self, message, level="INFO"):
        """
        Log a general message to the application log file.
        
        Args:
            message (str): The message to log
            level (str): The log level (INFO, WARNING, etc.)
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        caller_info = self._get_caller_info()
        log_path = os.path.join(self.log_dir, "application.log")
        
        try:
            # Append to existing log file or create new one
            with open(log_path, 'a') as log_file:
                log_file.write(f"[{timestamp}] [{level}] [{caller_info}] {message}\n")
        except Exception as e:
            print(f"Failed to write message log: {e}")

# Create a global logger instance
logger = Logger()
