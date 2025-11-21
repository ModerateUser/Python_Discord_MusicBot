"""
Input validation utilities for Discord Music Bot
Provides centralized validation for user inputs to prevent security issues
"""
import re
import math
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from core.exceptions import (
    InvalidQueryError,
    InvalidParameterError,
    InvalidVolumeError,
    PathTraversalError,
    InputValidationError,
)


# Constants
MAX_QUERY_LENGTH = 500
MAX_PLAYLIST_NAME_LENGTH = 50
MAX_SEARCH_QUERY_LENGTH = 100
MIN_VOLUME = 0
MAX_VOLUME = 100
MIN_DURATION = 10
MAX_DURATION = 300
MIN_PLAYLIST_COUNT = 1
MAX_PLAYLIST_COUNT = 50
MIN_SIMILAR_SONGS = 1
MAX_SIMILAR_SONGS = 20
MIN_TRANSITION_SONGS = 3
MAX_TRANSITION_SONGS = 30

# Regex patterns
VALID_PLAYLIST_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s_-]{1,50}$')
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


def validate_query(query: str, max_length: int = MAX_QUERY_LENGTH) -> str:
    """
    Validate search/play query
    
    Args:
        query: Query string to validate
        max_length: Maximum allowed length
        
    Returns:
        Validated and sanitized query
        
    Raises:
        InvalidQueryError: If query is invalid
    """
    if not query:
        raise InvalidQueryError("Query cannot be empty")
    
    query = query.strip()
    
    if len(query) > max_length:
        raise InvalidQueryError(
            f"Query too long (max {max_length} characters)",
            details={"length": len(query), "max": max_length}
        )
    
    # Check for null bytes (security)
    if '\x00' in query:
        raise InvalidQueryError("Query contains invalid characters")
    
    return query


def validate_search_query(query: str) -> str:
    """
    Validate search query (stricter than play query)
    
    Args:
        query: Search query to validate
        
    Returns:
        Validated query
        
    Raises:
        InvalidQueryError: If query is invalid
    """
    return validate_query(query, max_length=MAX_SEARCH_QUERY_LENGTH)


def validate_volume(volume: int) -> int:
    """
    Validate volume level
    
    Args:
        volume: Volume level to validate
        
    Returns:
        Validated volume level
        
    Raises:
        InvalidVolumeError: If volume is invalid
    """
    if not isinstance(volume, (int, float)):
        raise InvalidVolumeError(
            f"Volume must be a number, got {type(volume).__name__}"
        )
    
    if not math.isfinite(volume):
        raise InvalidVolumeError(
            f"Volume must be a finite number, got {volume}"
        )
    
    volume = int(volume)
    
    if not MIN_VOLUME <= volume <= MAX_VOLUME:
        raise InvalidVolumeError(
            f"Volume must be between {MIN_VOLUME} and {MAX_VOLUME}",
            details={"volume": volume, "min": MIN_VOLUME, "max": MAX_VOLUME}
        )
    
    return volume


def validate_playlist_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate playlist name for security
    
    Args:
        name: Playlist name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Playlist name cannot be empty"
    
    name = name.strip()
    
    if len(name) > MAX_PLAYLIST_NAME_LENGTH:
        return False, f"Playlist name must be {MAX_PLAYLIST_NAME_LENGTH} characters or less"
    
    if not VALID_PLAYLIST_NAME_PATTERN.match(name):
        return False, "Playlist name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    # Prevent path traversal attempts
    if '..' in name or '/' in name or '\\' in name:
        return False, "Invalid characters in playlist name"
    
    return True, None


def validate_file_path(filepath: str, allowed_directory: Optional[str] = None) -> str:
    """
    Validate file path for security
    
    Args:
        filepath: File path to validate
        allowed_directory: Optional directory to restrict access to
        
    Returns:
        Resolved absolute path
        
    Raises:
        PathTraversalError: If path traversal is detected
        InvalidParameterError: If path is invalid
    """
    if not filepath:
        raise InvalidParameterError("File path cannot be empty")
    
    try:
        # Resolve to absolute path
        path = Path(filepath).resolve()
        
        # Check for path traversal
        if '..' in filepath or filepath.startswith('/') or ':' in filepath[1:3]:
            # Allow absolute paths but check them carefully
            pass
        
        # If allowed_directory is specified, ensure path is within it
        if allowed_directory:
            allowed_path = Path(allowed_directory).resolve()
            try:
                path.relative_to(allowed_path)
            except ValueError:
                raise PathTraversalError(
                    "File path outside allowed directory",
                    details={"path": str(path), "allowed": str(allowed_path)}
                )
        
        return str(path)
        
    except Exception as e:
        if isinstance(e, (PathTraversalError, InvalidParameterError)):
            raise
        raise InvalidParameterError(f"Invalid file path: {e}")


def validate_url(url: str) -> str:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL
        
    Raises:
        InvalidParameterError: If URL is invalid
    """
    if not url:
        raise InvalidParameterError("URL cannot be empty")
    
    url = url.strip()
    
    # Check length
    if len(url) > MAX_QUERY_LENGTH:
        raise InvalidParameterError(
            f"URL too long (max {MAX_QUERY_LENGTH} characters)"
        )
    
    # Check format
    if not URL_PATTERN.match(url):
        raise InvalidParameterError("Invalid URL format")
    
    # Parse and validate
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise InvalidParameterError("Invalid URL structure")
    except Exception:
        raise InvalidParameterError("Failed to parse URL")
    
    return url


def validate_duration(duration: int, min_val: int = MIN_DURATION, max_val: int = MAX_DURATION) -> int:
    """
    Validate duration parameter
    
    Args:
        duration: Duration in seconds
        min_val: Minimum allowed duration
        max_val: Maximum allowed duration
        
    Returns:
        Validated duration
        
    Raises:
        InvalidParameterError: If duration is invalid
    """
    if not isinstance(duration, (int, float)):
        raise InvalidParameterError(
            f"Duration must be a number, got {type(duration).__name__}"
        )
    
    duration = int(duration)
    
    if not min_val <= duration <= max_val:
        raise InvalidParameterError(
            f"Duration must be between {min_val} and {max_val} seconds",
            details={"duration": duration, "min": min_val, "max": max_val}
        )
    
    return duration


def validate_count(count: int, min_val: int, max_val: int, name: str = "count") -> int:
    """
    Validate count parameter (generic)
    
    Args:
        count: Count value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Parameter name for error messages
        
    Returns:
        Validated count
        
    Raises:
        InvalidParameterError: If count is invalid
    """
    if not isinstance(count, int):
        raise InvalidParameterError(
            f"{name} must be an integer, got {type(count).__name__}"
        )
    
    if not min_val <= count <= max_val:
        raise InvalidParameterError(
            f"{name} must be between {min_val} and {max_val}",
            details={name: count, "min": min_val, "max": max_val}
        )
    
    return count


def validate_playlist_count(count: int) -> int:
    """Validate playlist song count"""
    return validate_count(
        count, 
        MIN_PLAYLIST_COUNT, 
        MAX_PLAYLIST_COUNT, 
        "Playlist count"
    )


def validate_similar_songs_count(count: int) -> int:
    """Validate similar songs count"""
    return validate_count(
        count,
        MIN_SIMILAR_SONGS,
        MAX_SIMILAR_SONGS,
        "Similar songs count"
    )


def validate_transition_duration(count: int) -> int:
    """Validate mood transition duration"""
    return validate_count(
        count,
        MIN_TRANSITION_SONGS,
        MAX_TRANSITION_SONGS,
        "Transition duration"
    )


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip whitespace
    text = text.strip()
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def is_url(text: str) -> bool:
    """
    Check if text is a URL
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be a URL
    """
    if not text:
        return False
    
    text = text.strip().lower()
    return text.startswith(('http://', 'https://', 'www.'))


def is_local_file_path(text: str) -> bool:
    """
    Check if text appears to be a local file path
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be a file path
    """
    if not text:
        return False
    
    # Check for path indicators
    return any([
        '/' in text,
        '\\' in text,
        ':' in text and len(text) > 2,  # Windows drive letter
        text.startswith('.'),  # Relative path
    ])


def validate_snowflake_id(snowflake_id: int, name: str = "ID") -> int:
    """
    Validate Discord snowflake ID
    
    Args:
        snowflake_id: Snowflake ID to validate
        name: Parameter name for error messages
        
    Returns:
        Validated snowflake ID
        
    Raises:
        InvalidParameterError: If ID is invalid
    """
    MIN_SNOWFLAKE = 10**16
    MAX_SNOWFLAKE = 10**19
    
    if not isinstance(snowflake_id, int):
        raise InvalidParameterError(
            f"{name} must be an integer, got {type(snowflake_id).__name__}"
        )
    
    if not MIN_SNOWFLAKE <= snowflake_id < MAX_SNOWFLAKE:
        raise InvalidParameterError(
            f"{name} is not a valid Discord snowflake ID (17-19 digits)",
            details={name: snowflake_id}
        )
    
    return snowflake_id


def validate_prompt(prompt: str, max_length: int = 500) -> str:
    """
    Validate AI prompt for synthesis or LLM
    
    Args:
        prompt: Prompt to validate
        max_length: Maximum allowed length
        
    Returns:
        Validated prompt
        
    Raises:
        InvalidParameterError: If prompt is invalid
    """
    if not prompt:
        raise InvalidParameterError("Prompt cannot be empty")
    
    prompt = sanitize_string(prompt, max_length)
    
    if not prompt:
        raise InvalidParameterError("Prompt cannot be empty after sanitization")
    
    return prompt
