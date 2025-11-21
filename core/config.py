"""
Configuration management with security enhancements
"""
import json
import os
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger('discord_bot')

# Constants
MIN_TOKEN_LENGTH = 50
MIN_SNOWFLAKE_ID = 10**16
MAX_SNOWFLAKE_ID = 10**19
DEFAULT_PLAYING = "!help for commands"
DEFAULT_PREFIX = "!"
DEFAULT_MAX_QUEUE_SIZE = 100
DEFAULT_MAX_PLAYLIST_SIZE = 500
DEFAULT_ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.opus']


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class Config:
    """Bot configuration with validation and security features"""
    
    def __init__(self, config_path: str = 'config.json') -> None:
        """
        Initialize configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path: str = config_path
        self.token: str = ""
        self.owner_id: int = 0
        self.playing: str = DEFAULT_PLAYING
        self.command_prefix: str = DEFAULT_PREFIX
        
        # Security settings
        self.max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE
        self.max_playlist_size: int = DEFAULT_MAX_PLAYLIST_SIZE
        self.allowed_file_extensions: List[str] = DEFAULT_ALLOWED_EXTENSIONS.copy()
        self.music_directory: Optional[str] = None
        
        self.load()
    
    def load(self) -> None:
        """Load configuration from file or environment variables"""
        # Try environment variables first (more secure)
        self.token = os.getenv('DISCORD_BOT_TOKEN', '')
        owner_id_env = os.getenv('DISCORD_OWNER_ID', '')
        self.playing = os.getenv('DISCORD_PLAYING', DEFAULT_PLAYING)
        self.command_prefix = os.getenv('DISCORD_PREFIX', DEFAULT_PREFIX)
        
        # If environment variables not set, try config file
        if not self.token and os.path.exists(self.config_path):
            self._load_from_file()
        elif owner_id_env:
            # Use environment variable for owner_id
            self.owner_id = self._parse_owner_id(owner_id_env)
        
        # Validate configuration
        self._validate()
    
    def _load_from_file(self) -> None:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                self.token = data.get('token', '')
                
                # Convert owner_id to int if it's a string
                owner_id_raw = data.get('owner_id', 0)
                self.owner_id = self._parse_owner_id(owner_id_raw)
                
                self.playing = data.get('playing', DEFAULT_PLAYING)
                self.command_prefix = data.get('command_prefix', DEFAULT_PREFIX)
                
                # Load security settings
                self.max_queue_size = data.get('max_queue_size', DEFAULT_MAX_QUEUE_SIZE)
                self.max_playlist_size = data.get('max_playlist_size', DEFAULT_MAX_PLAYLIST_SIZE)
                self.allowed_file_extensions = data.get(
                    'allowed_file_extensions', 
                    DEFAULT_ALLOWED_EXTENSIONS.copy()
                )
                self.music_directory = data.get('music_directory')
                
                logger.info(f"Configuration loaded from {self.config_path}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file: {e}")
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
        except IOError as e:
            logger.error(f"Failed to read config file: {e}")
            raise ConfigurationError(f"Cannot read config file: {e}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    def _parse_owner_id(self, owner_id_raw) -> int:
        """
        Parse owner ID from various formats
        
        Args:
            owner_id_raw: Raw owner ID (int or string)
            
        Returns:
            Parsed integer owner ID
            
        Raises:
            ConfigurationError: If owner ID is invalid
        """
        if isinstance(owner_id_raw, int):
            return owner_id_raw
        
        if isinstance(owner_id_raw, str):
            try:
                return int(owner_id_raw)
            except ValueError:
                logger.error(f"Invalid owner_id format: {owner_id_raw}")
                raise ConfigurationError(f"Invalid owner_id: {owner_id_raw}")
        
        logger.error(f"Invalid owner_id type: {type(owner_id_raw).__name__}")
        raise ConfigurationError(f"owner_id must be int or string, got {type(owner_id_raw).__name__}")
    
    def _validate(self) -> None:
        """Validate configuration with security checks"""
        errors: List[str] = []
        
        # Validate token
        if not self.token:
            errors.append("Bot token is required (set DISCORD_BOT_TOKEN or add to config.json)")
        elif len(self.token) < MIN_TOKEN_LENGTH:
            errors.append(f"Bot token appears invalid (minimum {MIN_TOKEN_LENGTH} characters)")
        
        # Validate owner_id
        if not self.owner_id:
            errors.append("Owner ID is required (set DISCORD_OWNER_ID or add to config.json)")
        elif not isinstance(self.owner_id, int):
            errors.append(f"Owner ID must be an integer, got {type(self.owner_id).__name__}")
        elif not self._is_valid_snowflake(self.owner_id):
            errors.append(f"Owner ID {self.owner_id} is not a valid Discord snowflake ID")
        
        # Validate music_directory if set
        if self.music_directory:
            music_path = Path(self.music_directory)
            if not music_path.exists():
                errors.append(f"music_directory does not exist: {self.music_directory}")
            elif not music_path.is_dir():
                errors.append(f"music_directory is not a directory: {self.music_directory}")
        
        # Validate limits
        if self.max_queue_size < 1:
            errors.append("max_queue_size must be at least 1")
        if self.max_playlist_size < 1:
            errors.append("max_playlist_size must be at least 1")
        
        # Validate file extensions
        if not self.allowed_file_extensions:
            errors.append("allowed_file_extensions cannot be empty")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        logger.info("Configuration validated successfully")
    
    def _is_valid_snowflake(self, snowflake_id: int) -> bool:
        """
        Validate Discord snowflake ID (17-19 digits)
        
        Args:
            snowflake_id: Discord snowflake ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        return MIN_SNOWFLAKE_ID <= snowflake_id < MAX_SNOWFLAKE_ID
    
    def is_owner(self, user_id: int) -> bool:
        """
        Check if user is the bot owner (type-safe comparison)
        
        Args:
            user_id: Discord user ID to check
            
        Returns:
            True if user is owner, False otherwise
        """
        return isinstance(user_id, int) and user_id == self.owner_id
    
    def is_file_allowed(self, filepath: str) -> bool:
        """
        Check if file is allowed to be played (security validation)
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file is allowed, False otherwise
        """
        try:
            path = Path(filepath).resolve()
            
            # Check file extension
            if path.suffix.lower() not in self.allowed_file_extensions:
                logger.warning(f"File extension not allowed: {path.suffix}")
                return False
            
            # Check if file exists
            if not path.exists():
                logger.warning(f"File does not exist: {filepath}")
                return False
            
            # Check if it's actually a file
            if not path.is_file():
                logger.warning(f"Path is not a file: {filepath}")
                return False
            
            # If music_directory is set, ensure file is within it
            if self.music_directory:
                music_dir = Path(self.music_directory).resolve()
                try:
                    path.relative_to(music_dir)
                except ValueError:
                    logger.warning(f"File outside music_directory: {filepath}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file {filepath}: {e}")
            return False


# Global config instance
config = Config()
