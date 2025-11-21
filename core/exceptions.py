"""
Custom Exception Hierarchy for Discord Music Bot
Provides clear, specific exceptions for better error handling
"""


class BotException(Exception):
    """Base exception for all bot-related errors"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# Configuration Exceptions
class ConfigurationError(BotException):
    """Raised when there's a configuration error"""
    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing"""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration values are invalid"""
    pass


# Service Exceptions
class ServiceError(BotException):
    """Base exception for service-related errors"""
    pass


class ServiceInitializationError(ServiceError):
    """Raised when a service fails to initialize"""
    pass


class ServiceUnavailableError(ServiceError):
    """Raised when a required service is unavailable"""
    pass


class ServiceTimeoutError(ServiceError):
    """Raised when a service operation times out"""
    pass


# Audio Exceptions
class AudioError(BotException):
    """Base exception for audio-related errors"""
    pass


class AudioSourceError(AudioError):
    """Raised when there's an error with the audio source"""
    pass


class AudioPlaybackError(AudioError):
    """Raised when there's an error during playback"""
    pass


class AudioDownloadError(AudioError):
    """Raised when audio download fails"""
    pass


class NoAudioSourceError(AudioError):
    """Raised when no audio source is available"""
    pass


# Queue Exceptions
class QueueError(BotException):
    """Base exception for queue-related errors"""
    pass


class QueueEmptyError(QueueError):
    """Raised when attempting to access an empty queue"""
    pass


class QueueFullError(QueueError):
    """Raised when attempting to add to a full queue"""
    pass


class InvalidQueueIndexError(QueueError):
    """Raised when queue index is out of bounds"""
    pass


# LLM/NLP Exceptions
class LLMError(BotException):
    """Base exception for LLM-related errors"""
    pass


class LLMResponseError(LLMError):
    """Raised when LLM response is invalid or malformed"""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out"""
    pass


class LLMAPIError(LLMError):
    """Raised when LLM API returns an error"""
    pass


class IntentParseError(LLMError):
    """Raised when intent parsing fails"""
    pass


# Validation Exceptions
class ValidationError(BotException):
    """Base exception for validation errors"""
    pass


class InvalidParameterError(ValidationError):
    """Raised when a parameter value is invalid"""
    pass


class MissingParameterError(ValidationError):
    """Raised when a required parameter is missing"""
    pass


class ParameterTypeError(ValidationError):
    """Raised when a parameter has the wrong type"""
    pass


# Voice/Connection Exceptions
class VoiceError(BotException):
    """Base exception for voice-related errors"""
    pass


class NotConnectedError(VoiceError):
    """Raised when bot is not connected to voice"""
    pass


class AlreadyConnectedError(VoiceError):
    """Raised when bot is already connected to voice"""
    pass


class VoiceConnectionError(VoiceError):
    """Raised when voice connection fails"""
    pass


class UserNotInVoiceError(VoiceError):
    """Raised when user is not in a voice channel"""
    pass


# Synthesis Exceptions
class SynthesisError(BotException):
    """Base exception for music synthesis errors"""
    pass


class SynthesisAPIError(SynthesisError):
    """Raised when synthesis API returns an error"""
    pass


class SynthesisTimeoutError(SynthesisError):
    """Raised when synthesis takes too long"""
    pass


class InvalidPromptError(SynthesisError):
    """Raised when synthesis prompt is invalid"""
    pass


# Playlist Exceptions
class PlaylistError(BotException):
    """Base exception for playlist-related errors"""
    pass


class PlaylistNotFoundError(PlaylistError):
    """Raised when playlist is not found"""
    pass


class PlaylistLoadError(PlaylistError):
    """Raised when playlist fails to load"""
    pass


class PlaylistSaveError(PlaylistError):
    """Raised when playlist fails to save"""
    pass


# Cache Exceptions
class CacheError(BotException):
    """Base exception for cache-related errors"""
    pass


class CacheExpiredError(CacheError):
    """Raised when cached item has expired"""
    pass


class CacheFullError(CacheError):
    """Raised when cache is full"""
    pass


# Action Execution Exceptions
class ActionExecutionError(BotException):
    """Base exception for action execution errors"""
    pass


class InvalidActionError(ActionExecutionError):
    """Raised when action type is invalid"""
    pass


class ActionParameterError(ActionExecutionError):
    """Raised when action parameters are invalid"""
    pass


class ActionTimeoutError(ActionExecutionError):
    """Raised when action execution times out"""
    pass


# Permission Exceptions
class PermissionError(BotException):
    """Base exception for permission-related errors"""
    pass


class InsufficientPermissionsError(PermissionError):
    """Raised when user lacks required permissions"""
    pass


class BotPermissionError(PermissionError):
    """Raised when bot lacks required permissions"""
    pass


# Rate Limiting Exceptions
class RateLimitError(BotException):
    """Base exception for rate limiting errors"""
    pass


class UserRateLimitError(RateLimitError):
    """Raised when user hits rate limit"""
    pass


class APIRateLimitError(RateLimitError):
    """Raised when external API rate limit is hit"""
    pass


# Utility function to get exception by name
def get_exception_class(name: str) -> type:
    """
    Get exception class by name
    
    Args:
        name: Exception class name
        
    Returns:
        Exception class
        
    Raises:
        ValueError: If exception class not found
    """
    import sys
    current_module = sys.modules[__name__]
    
    if hasattr(current_module, name):
        exc_class = getattr(current_module, name)
        if isinstance(exc_class, type) and issubclass(exc_class, BotException):
            return exc_class
    
    raise ValueError(f"Exception class not found: {name}")


# Exception hierarchy for reference
EXCEPTION_HIERARCHY = {
    'BotException': [
        'ConfigurationError',
        'ServiceError',
        'AudioError',
        'QueueError',
        'LLMError',
        'ValidationError',
        'VoiceError',
        'SynthesisError',
        'PlaylistError',
        'CacheError',
        'ActionExecutionError',
        'PermissionError',
        'RateLimitError',
    ]
}
