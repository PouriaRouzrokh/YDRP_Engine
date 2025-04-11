import logging
import os
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


class BackendLogger:
    """Custom logger class for the backend using Rich for formatting and file output"""
    
    def __init__(self, name: str = "BackendLogger", level: int = logging.INFO, path: Optional[str] = None):
        """Initialize the logger with Rich formatting and file output

        Args:
            name: The name of the logger
            level: The logging level (default: logging.INFO)
            path: Optional file path to save logs. If None, logs will only be displayed in the console
        """
        # Create a Rich console
        self.console = Console()
        
        # Create the logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove any existing handlers to avoid duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Add Rich handler for terminal output with nice formatting
        rich_handler = RichHandler(
            rich_tracebacks=True,
            console=self.console,
            show_time=True,
            show_path=False
        )
        rich_handler.setLevel(level)
        self.logger.addHandler(rich_handler)
        
        # Add file handler if a log file is specified
        if path and path != "":
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Standard formatter for file logs
                file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                
                # Create and configure file handler
                file_handler = logging.FileHandler(
                    path, 
                    mode='a' if os.path.exists(path) else 'w', 
                    encoding='utf-8'
                )
                file_handler.setFormatter(file_formatter)
                file_handler.setLevel(level)
                
                # Add file handler to the logger
                self.logger.addHandler(file_handler)
                
                # Log that we initialized with a file
                self.logger.info(f"Backend logging initialized. Log file: {path}")
            except Exception as e:
                self.logger.error(f"Failed to initialize file logging to {path}: {e}", exc_info=True)
                self.logger.info("Backend logging initialized (console only)")
        else:
            self.logger.info("Backend logging initialized (console only)")

    def info(self, message: str) -> None:
        """Log info level message"""
        self.logger.info(message)
        
    def error(self, message: str, exc_info=False) -> None:
        """Log error level message"""
        self.logger.error(message, exc_info=exc_info)
        
    def debug(self, message: str) -> None:
        """Log debug level message"""
        self.logger.debug(message)
        
    def warning(self, message: str) -> None:
        """Log warning level message"""
        self.logger.warning(message)
    
    def success(self, message: str) -> None:
        """Log success as an info message with success prefix"""
        self.logger.info(f"[green]SUCCESS:[/green] {message}")
        
    def failure(self, message: str) -> None:
        """Log failure as an error message with failure prefix"""
        self.logger.error(f"[red]FAILURE:[/red] {message}")
        
    def progress(self, message: str) -> None:
        """Log progress as an info message with progress prefix"""
        self.logger.info(f"[blue]PROGRESS:[/blue] {message}")
        
    def db(self, message: str) -> None:
        """Log database-related message with special formatting"""
        self.logger.info(f"[yellow]DATABASE:[/yellow] {message}")
        
    def api(self, message: str) -> None:
        """Log API-related message with special formatting"""
        self.logger.info(f"[magenta]API:[/magenta] {message}")
        
    def vector(self, message: str) -> None:
        """Log vector operations with special formatting"""
        self.logger.info(f"[cyan]VECTOR:[/cyan] {message}")


# Create a default instance for import
logger = BackendLogger(path=os.path.join("data", "logs", "backend.log"))