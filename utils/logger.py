"""
Logging configuration with enhanced features
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_NAME = 'discord_bot'
DEFAULT_LOG_DIR = 'logs'
DEFAULT_LOG_FILE = 'bot.log'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Keep 5 backup files

# Log format strings
CONSOLE_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
FILE_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logger(
    name: str = DEFAULT_LOG_NAME,
    level: int = DEFAULT_LOG_LEVEL,
    log_dir: str = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = MAX_LOG_SIZE,
    backup_count: int = BACKUP_COUNT
) -> logging.Logger:
    """
    Setup and configure logger with console and file handlers
    
    Args:
        name: Logger name
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_dir: Directory for log files
        log_file: Log file name
        console_output: Enable console logging
        file_output: Enable file logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    console_formatter = logging.Formatter(
        CONSOLE_FORMAT,
        datefmt=DATE_FORMAT
    )
    
    file_formatter = logging.Formatter(
        FILE_FORMAT,
        datefmt=DATE_FORMAT
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True, parents=True)
        
        file_handler = RotatingFileHandler(
            log_path / log_file,
            encoding='utf-8',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    logger.info(f"Logger '{name}' initialized with level {logging.getLevelName(level)}")
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get an existing logger or create a new one
    
    Args:
        name: Logger name (defaults to DEFAULT_LOG_NAME)
        
    Returns:
        Logger instance
    """
    logger_name = name or DEFAULT_LOG_NAME
    logger = logging.getLogger(logger_name)
    
    # If logger has no handlers, set it up
    if not logger.handlers:
        return setup_logger(logger_name)
    
    return logger


def set_log_level(level: int, logger_name: str = DEFAULT_LOG_NAME) -> None:
    """
    Change the log level of an existing logger
    
    Args:
        level: New logging level
        logger_name: Name of the logger to modify
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.info(f"Log level changed to {logging.getLevelName(level)}")
