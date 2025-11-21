"""
Logging configuration utility - FIXED VERSION
FIX #11: Logger duplicate handler bug - allow level changes
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Optional

# Configuration constants
LOG_DIR = 'logs'
LOG_FILE = 'discord_bot.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
CONSOLE_FORMAT = '%(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Rotation settings
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Keep 5 backup files

# Default log level
DEFAULT_LEVEL = logging.INFO


def setup_logger(
    name: str = 'discord_bot',
    level: int = DEFAULT_LEVEL,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup and configure logger with rotating file handler
    
    FIX #11: Always update log level, even if handlers exist
    
    Args:
        name: Logger name
        level: Logging level (e.g., logging.INFO)
        log_file: Optional custom log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # FIX #11: Always set the level, even if handlers exist
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        # Update existing handlers' levels
        for handler in logger.handlers:
            handler.setLevel(level)
        return logger
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Determine log file path
    if log_file is None:
        log_file = os.path.join(LOG_DIR, LOG_FILE)
    
    # Create formatters
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_formatter = logging.Formatter(CONSOLE_FORMAT)
    
    # Create rotating file handler
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except (IOError, OSError) as e:
        print(f"Warning: Could not create log file handler: {e}")
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = 'discord_bot') -> logging.Logger:
    """
    Get an existing logger or create a new one
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


def set_log_level(level: int, name: str = 'discord_bot') -> None:
    """
    Change the log level for an existing logger
    
    FIX #11: Properly update level for logger and all handlers
    
    Args:
        level: New logging level (e.g., logging.DEBUG)
        name: Logger name
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Update all handlers
    for handler in logger.handlers:
        handler.setLevel(level)
    
    logger.info(f"Log level changed to {logging.getLevelName(level)}")


def add_file_handler(
    logger: logging.Logger,
    log_file: str,
    level: Optional[int] = None,
    max_bytes: int = MAX_LOG_SIZE,
    backup_count: int = BACKUP_COUNT
) -> None:
    """
    Add an additional file handler to a logger
    
    Args:
        logger: Logger instance
        log_file: Path to log file
        level: Optional log level (uses logger's level if not specified)
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep
    """
    if level is None:
        level = logger.level
    
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.info(f"Added file handler: {log_file}")
    except (IOError, OSError) as e:
        logger.error(f"Failed to add file handler {log_file}: {e}")


def remove_all_handlers(name: str = 'discord_bot') -> None:
    """
    Remove all handlers from a logger
    
    Args:
        name: Logger name
    """
    logger = logging.getLogger(name)
    
    for handler in logger.handlers[:]:  # Copy list to avoid modification during iteration
        handler.close()
        logger.removeHandler(handler)
