"""
Custom exception hierarchy for Discord Music Bot
Provides specific exception types for better error handling and debugging
"""


class BotException(Exception):
    """Base exception for all bot-related errors"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Configuration Exceptions
class ConfigurationError(BotException):
    """Raised when configuration is invalid or missing"""
    pass


class ConfigValidationError(ConfigurationError):
    """Raised when configuration validation fails"""
    pass


class ConfigLoadError(ConfigurationError):
    """Raised when configuration cannot be loaded"""
    pass


# Audio Service Exceptions
class AudioServiceError(BotException):
    """Base exception for audio service errors"""
    pass


class FFmpegNotFoundError(AudioServiceError):
    """Raised when FFmpeg is not available"""
    pass


class AudioSourceError(AudioServiceError):
    """Raised when audio source creation fails"""
    pass


class StreamExtractionError(AudioServiceError):
    """Raised when stream extraction fails"""
    pass


class AudioTimeoutError(AudioServiceError):
    """Raised when audio operation times out"""
    pass


# Playback Exceptions
class PlaybackError(BotException):
    """Base exception for playback errors"""
    pass


class QueueFullError(PlaybackError):
    """Raised when queue is at maximum capacity"""
    pass


class QueueEmptyError(PlaybackError):
    """Raised when attempting to play from empty queue"""
    pass


class VoiceConnectionError(PlaybackError):
    """Raised when voice connection fails"""
    pass


class PlaybackTimeoutError(PlaybackError):
    """Raised when playback operation times out"""
    pass


# Playlist Exceptions
class PlaylistError(BotException):
    """Base exception for playlist errors"""
    pass


class PlaylistNotFoundError(PlaylistError):
    """Raised when playlist doesn't exist"""
    pass


class PlaylistExistsError(PlaylistError):
    """Raised when attempting to create duplicate playlist"""
    pass


class PlaylistFullError(PlaylistError):
    """Raised when playlist is at maximum capacity"""
    pass


class PlaylistSaveError(PlaylistError):
    """Raised when playlist save operation fails"""
    pass


# AI/LLM Exceptions
class AIServiceError(BotException):
    """Base exception for AI service errors"""
    pass


class LLMNotAvailableError(AIServiceError):
    """Raised when LLM service is not available"""
    pass


class LLMResponseError(AIServiceError):
    """Raised when LLM response is invalid or malformed"""
    pass


class LLMTimeoutError(AIServiceError):
    """Raised when LLM request times out"""
    pass


class IntentParseError(AIServiceError):
    """Raised when natural language intent parsing fails"""
    pass


# Music Synthesis Exceptions
class SynthesisError(BotException):
    """Base exception for music synthesis errors"""
    pass


class SynthesisNotAvailableError(SynthesisError):
    """Raised when synthesis service is not available"""
    pass


class SynthesisTimeoutError(SynthesisError):
    """Raised when synthesis operation times out"""
    pass


class SynthesisBackendError(SynthesisError):
    """Raised when synthesis backend fails"""
    pass


# Security Exceptions
class SecurityError(BotException):
    """Base exception for security-related errors"""
    pass


class PathTraversalError(SecurityError):
    """Raised when path traversal attempt is detected"""
    pass


class InvalidFileError(SecurityError):
    """Raised when file validation fails"""
    pass


class RateLimitError(SecurityError):
    """Raised when rate limit is exceeded"""
    pass


class InputValidationError(SecurityError):
    """Raised when user input validation fails"""
    pass


# Permission Exceptions
class PermissionError(BotException):
    """Base exception for permission errors"""
    pass


class OwnerOnlyError(PermissionError):
    """Raised when non-owner attempts owner-only action"""
    pass


class InsufficientPermissionsError(PermissionError):
    """Raised when user lacks required permissions"""
    pass


# Resource Exceptions
class ResourceError(BotException):
    """Base exception for resource management errors"""
    pass


class ResourceNotFoundError(ResourceError):
    """Raised when required resource is not found"""
    pass


class ResourceCleanupError(ResourceError):
    """Raised when resource cleanup fails"""
    pass


class ResourceExhaustedError(ResourceError):
    """Raised when resource limit is reached"""
    pass


# Validation Exceptions
class ValidationError(BotException):
    """Base exception for validation errors"""
    pass


class InvalidParameterError(ValidationError):
    """Raised when parameter validation fails"""
    pass


class InvalidQueryError(ValidationError):
    """Raised when query validation fails"""
    pass


class InvalidVolumeError(ValidationError):
    """Raised when volume value is invalid"""
    pass


# Helper Functions
def format_exception_message(exc: BotException) -> str:
    """
    Format exception message with details for logging
    
    Args:
        exc: Exception to format
        
    Returns:
        Formatted message string
    """
    msg = f"{exc.__class__.__name__}: {exc.message}"
    if exc.details:
        details_str = ", ".join(f"{k}={v}" for k, v in exc.details.items())
        msg += f" ({details_str})"
    return msg


def is_retryable_error(exc: Exception) -> bool:
    """
    Check if an error is retryable
    
    Args:
        exc: Exception to check
        
    Returns:
        True if error is retryable
    """
    retryable_types = (
        AudioTimeoutError,
        LLMTimeoutError,
        SynthesisTimeoutError,
        PlaybackTimeoutError,
        StreamExtractionError,
    )
    return isinstance(exc, retryable_types)


def get_user_friendly_message(exc: Exception) -> str:
    """
    Get user-friendly error message
    
    Args:
        exc: Exception to convert
        
    Returns:
        User-friendly message
    """
    error_messages = {
        FFmpegNotFoundError: "❌ Audio system not available. Please contact bot administrator.",
        QueueFullError: "❌ Queue is full! Please wait for some songs to finish.",
        PlaylistNotFoundError: "❌ Playlist not found. Use `!playlist list` to see available playlists.",
        LLMNotAvailableError: "❌ AI features are currently unavailable. Use regular commands instead.",
        SynthesisNotAvailableError: "❌ Music synthesis is not enabled. Check configuration.",
        PathTraversalError: "❌ Invalid file path detected.",
        RateLimitError: "⏳ You're doing that too fast! Please slow down.",
        VoiceConnectionError: "❌ Could not connect to voice channel. Check bot permissions.",
        AudioTimeoutError: "⏳ Audio operation timed out. Please try again.",
        InvalidQueryError: "❌ Invalid search query. Please check your input.",
    }
    
    for exc_type, message in error_messages.items():
        if isinstance(exc, exc_type):
            return message
    
    # Default message
    if isinstance(exc, BotException):
        return f"❌ {exc.message}"
    
    return "❌ An unexpected error occurred. Please try again."
