"""
Clean Terminal UI System
Inspired by Claude Code's design principles
"""
import logging
from typing import Optional, Dict
from enum import Enum
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
import sys
import os

# Initialize colorama for Windows support
if sys.platform == "win32":
    try:
        from colorama import init
        init()
    except ImportError:
        pass


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class TerminalUI:
    """Clean terminal interface without emojis"""
    
    def __init__(self):
        # Configure console for Windows compatibility
        if sys.platform == "win32":
            # Force UTF-8 encoding on Windows
            os.environ["PYTHONIOENCODING"] = "utf-8"
            self.console = Console(
                force_terminal=True,
                legacy_windows=False,  # Use new Windows terminal features if available
                no_color=False,
                force_interactive=True
            )
        else:
            self.console = Console(file=sys.stdout, force_terminal=True)
        self._setup_colors()
    
    def _setup_colors(self):
        """Define color scheme similar to Claude Code"""
        self.colors = {
            LogLevel.DEBUG: "dim cyan",
            LogLevel.INFO: "white",
            LogLevel.SUCCESS: "green",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red"
        }
        
        self.prefixes = {
            LogLevel.DEBUG: "[DEBUG]",
            LogLevel.INFO: "[INFO]", 
            LogLevel.SUCCESS: "[SUCCESS]",
            LogLevel.WARNING: "[WARNING]",
            LogLevel.ERROR: "[ERROR]"
        }
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO, component: Optional[str] = None):
        """Log a message with clean formatting"""
        prefix = self.prefixes[level]
        color = self.colors[level]
        
        if component:
            formatted_message = f"{prefix} [{component}] {message}"
        else:
            formatted_message = f"{prefix} {message}"
        
        text = Text(formatted_message, style=color)
        self.console.print(text)
    
    def debug(self, message: str, component: Optional[str] = None):
        """Debug level message"""
        self.log(message, LogLevel.DEBUG, component)
    
    def info(self, message: str, component: Optional[str] = None):
        """Info level message"""
        self.log(message, LogLevel.INFO, component)
    
    def success(self, message: str, component: Optional[str] = None):
        """Success level message"""
        self.log(message, LogLevel.SUCCESS, component)
    
    def warning(self, message: str, component: Optional[str] = None):
        """Warning level message"""
        self.log(message, LogLevel.WARNING, component)
    
    def error(self, message: str, component: Optional[str] = None):
        """Error level message"""
        self.log(message, LogLevel.ERROR, component)
    
    def panel(self, content: str, title: Optional[str] = None, style: str = "blue"):
        """Display content in a clean panel"""
        panel = Panel(
            content,
            title=title,
            border_style=style,
            box=box.ROUNDED,
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def ascii_logo(self):
        """Display ASCII art logo for Claudable - Windows compatible"""
        # Use simple ASCII art that works on Windows
        self.console.print()
        self.console.print("[bold rgb(182,109,77)]   _____ _                 _       _     _      [/bold rgb(182,109,77)]")
        self.console.print("[bold rgb(182,109,77)]  / ____| |               | |     | |   | |     [/bold rgb(182,109,77)]")
        self.console.print("[bold rgb(182,109,77)] | |    | | __ _ _   _  __| | __ _| |__ | | ___ [/bold rgb(182,109,77)]")
        self.console.print("[bold rgb(182,109,77)] | |    | |/ _` | | | |/ _` |/ _` | '_ \\| |/ _ \\[/bold rgb(182,109,77)]")
        self.console.print("[bold rgb(182,109,77)] | |____| | (_| | |_| | (_| | (_| | |_) | |  __/[/bold rgb(182,109,77)]")
        self.console.print("[bold rgb(182,109,77)]  \\_____|_|\\__,_|\\__,_|\\__,_|\\__,_|_.__/|_|\\___|[/bold rgb(182,109,77)]")
        self.console.print()
        
        # Tagline
        self.console.print("[rgb(182,109,77)]Connect Claude Code. Build what you want. Deploy instantly.[/rgb(182,109,77)]")
        self.console.print()
    
    def status_line(self, items: Dict[str, str]):
        """Display a status line with key-value pairs"""
        table = Table.grid(padding=1)
        
        for key, value in items.items():
            table.add_column()
            table.add_column()
        
        keys = list(items.keys())
        values = list(items.values())
        
        # Add keys row
        table.add_row(*[Text(key, style="dim cyan") for key in keys])
        # Add values row  
        table.add_row(*[Text(value, style="white") for value in values])
        
        self.console.print(table)
    
    def connection_status(self, project_id: str, status: str):
        """WebSocket connection status"""
        self.log(f"WebSocket {status} for project: {project_id}", LogLevel.INFO, "WebSocket")
    
    def session_info(self, session_id: str, cli_type: str, model: str):
        """CLI session information"""
        self.log(f"Session {session_id[:8]}... started with {cli_type} using {model}", LogLevel.INFO, "Session")
    
    def operation_result(self, operation: str, success: bool, details: Optional[str] = None):
        """Operation result with clean formatting"""
        level = LogLevel.SUCCESS if success else LogLevel.ERROR
        message = f"{operation} {'completed' if success else 'failed'}"
        if details:
            message += f": {details}"
        self.log(message, level)


# Global instance
ui = TerminalUI()


class TerminalUIHandler(logging.Handler):
    """Custom logging handler that uses TerminalUI"""
    
    def __init__(self):
        super().__init__()
        self.ui = ui
    
    def emit(self, record):
        """Emit a log record using TerminalUI"""
        try:
            level_map = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.ERROR
            }
            
            level = level_map.get(record.levelno, LogLevel.INFO)
            component = record.name if record.name != "root" else None
            
            self.ui.log(record.getMessage(), level, component)
        except Exception:
            self.handleError(record)