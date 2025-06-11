import threading
from typing import Any, Callable

# Constants
TIMEOUT_SECONDS = 5  # Default timeout in seconds

class TimeoutError(Exception):
    """Exception raised when a function execution times out"""
    pass

class FunctionWithTimeout:
    """Utility class to run functions with a timeout using threads"""
    
    def __init__(self, timeout: float = TIMEOUT_SECONDS):
        self.timeout = timeout
        self.result = None
        self.exception = None
        self._thread = None
    
    def run_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Run a function with a timeout using thread-based approach (all platforms)
        
        Args:
            func: The function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function or an exception if timeout or error occurred
        """
        self.exception = None
        self.result = None
        
        def worker():
            try:
                self.result = func(*args, **kwargs)
            except Exception as e:
                self.exception = e
        
        # Create and start the thread
        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.daemon = True  # Ensure thread doesn't prevent program exit
        self._thread.start()
        
        # Wait with timeout and check if thread is still running
        self._thread.join(self.timeout)
        
        if self._thread.is_alive():
            # Thread is still running after timeout
            # Note: We can't forcibly terminate a thread in Python, but marking as daemon
            # ensures it won't prevent program exit
            return TimeoutError("Operation timed out")
        
        if self.exception:
            # Re-raise any exception that occurred in the thread
            return self.exception
        
        return self.result 