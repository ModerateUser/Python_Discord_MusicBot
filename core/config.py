"""
Configuration management with security enhancements - FIXED VERSION
FIX #12: Config validation timing - graceful error handling
FIX #2: Added to_dict() method for proper config passing
FIX #3: Added missing music_synthesis, llm, and llm_config fields
FIX CONFIG #3: Fixed get_config_template() to match config.example.json
FIX CONFIG #4: Resolve config.json path relative to project root, not CWD
"""
import json
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Initialize logger early, before config validation
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


def get_project_root() -> Path:
    """
    FIX CONFIG #4: Get the project root directory
    This ensures config.json is always loaded from the project root,
    regardless of the current working directory.
    
    Returns:
        Path to project root (where bot.py is located)
    """
    # This file is in core/config.py, so project root is parent of parent
    return Path(__file__).parent.parent.resolve()


class Config:
    """
    Bot configuration with validation and security features
    FIX #12: Graceful error handling with helpful messages
    FIX #2: Added to_dict() method
    FIX #3: Added missing fields
    FIX CONFIG #3: Fixed template generation
    FIX CONFIG #4: Resolve config path relative to project root
    """
    
    def __init__(self, config_path: str = 'config.json', validate: bool = True) -> None:
        """
        Initialize configuration
        
        FIX #12: Add validate parameter to allow deferred validation
        FIX CONFIG #4: Resolve config_path relative to project root
        
        Args:
            config_path: Path to configuration file (relative to project root)
            validate: Whether to validate immediately (default True)
        """
        # FIX CONFIG #4: Resolve config path relative to project root
        if not os.path.isabs(config_path):
            self.config_path = str(get_project_root() / config_path)
        else:
            self.config_path = config_path
        
        self.token: str = ""
        self.owner_id: int = 0
        self.playing: str = DEFAULT_PLAYING
        self.command_prefix: str = DEFAULT_PREFIX
        
        # Security settings
        self.max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE
        self.max_playlist_size: int = DEFAULT_MAX_PLAYLIST_SIZE
        self.allowed_file_extensions: List[str] = DEFAULT_ALLOWED_EXTENSIONS.copy()
        self.music_directory: Optional[str] = None
        
        # FIX #3: Add LLM configuration fields (matching config.example.json)
        self.llm: Dict[str, Any] = {
            'enabled': False,
            'provider': 'ollama',
            'model': 'llama3',
            'api_key': None,
            'base_url': 'http://localhost:11434',
            'timeout': 30,
            'max_tokens': 500
        }
        self.llm_config: Optional[Dict[str, Any]] = None
        
        # FIX #3: Add music synthesis configuration (matching config.example.json)
        self.music_synthesis: Dict[str, Any] = {
            'enabled': False,
            'backend': 'disabled',
            'cache_dir': 'generated_music',
            'max_cache_size_mb': 1000,
            'default_duration': 30,
            'default_quality': 'medium',
            'suno_api_key': None,
            'suno_api_url': 'https://api.suno.ai/v1',
            'musicgen_model': 'facebook/musicgen-small'
        }
        
        # FIX CONFIG #3: Add web_dashboard configuration
        self.web_dashboard: Dict[str, Any] = {
            'enabled': True,
            'host': '0.0.0.0',
            'port': 8000
        }
        
        # FIX #12: Track validation state
        self._validated: bool = False
        
        try:
            self.load()
            if validate:
                self._validate()
        except ConfigurationError:
            # Re-raise with helpful context
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise ConfigurationError(f"Failed to initialize configuration: {e}")
    
    def load(self) -> None:
        """
        Load configuration from file or environment variables
        FIX #12: Better error messages for common issues
        FIX CONFIG #4: Show resolved config path in messages
        """
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
            try:
                self.owner_id = self._parse_owner_id(owner_id_env)
            except ConfigurationError as e:
                # Provide helpful error message
                raise ConfigurationError(
                    f"Invalid DISCORD_OWNER_ID environment variable: {e}\n"
                    f"Please set a valid Discord user ID (17-19 digit number)"
                )
    
    def _load_from_file(self) -> None:
        """
        Load configuration from JSON file
        FIX #12: Detailed error messages for file issues
        FIX #3: Load LLM and music synthesis config
        FIX CONFIG #3: Load web_dashboard config
        FIX CONFIG #4: Show absolute path in log messages
        """
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
                
                # FIX #3: Load LLM configuration
                if 'llm' in data:
                    self.llm.update(data['llm'])
                    self.llm_config = data['llm']
                
                # FIX #3: Load music synthesis configuration
                if 'music_synthesis' in data:
                    self.music_synthesis.update(data['music_synthesis'])
                
                # FIX CONFIG #3: Load web_dashboard configuration
                if 'web_dashboard' in data:
                    self.web_dashboard.update(data['web_dashboard'])
                
                logger.info(f"Configuration loaded from {self.config_path}")
                
        except json.JSONDecodeError as e:
            # FIX #12: Helpful error message for JSON syntax errors
            raise ConfigurationError(
                f"Invalid JSON in config file '{self.config_path}':\n"
                f"  Error: {e}\n"
                f"  Line {e.lineno}, Column {e.colno}\n"
                f"  Please check your JSON syntax (commas, quotes, brackets)"
            )
        except FileNotFoundError:
            # FIX #12: Helpful message for missing config file
            # FIX CONFIG #4: Show both relative and absolute paths
            raise ConfigurationError(
                f"Config file not found: {self.config_path}\n"
                f"  Project root: {get_project_root()}\n"
                f"  Looking for: config.json in project root\n"
                f"  Current working directory: {os.getcwd()}\n\n"
                f"Please create a config.json file in the project root or set environment variables:\n"
                f"  - DISCORD_BOT_TOKEN\n"
                f"  - DISCORD_OWNER_ID"
            )
        except IOError as e:
            # FIX #12: Helpful message for permission issues
            raise ConfigurationError(
                f"Cannot read config file '{self.config_path}': {e}\n"
                f"Please check file permissions"
            )
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}", exc_info=True)
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
                raise ConfigurationError(
                    f"Invalid owner_id format: '{owner_id_raw}'\n"
                    f"Owner ID must be a number (Discord user ID)"
                )
        
        raise ConfigurationError(
            f"owner_id must be int or string, got {type(owner_id_raw).__name__}"
        )
    
    def _validate(self) -> None:
        """
        Validate configuration with security checks
        FIX #12: Collect all errors and show them together
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Validate token
        if not self.token:
            errors.append(
                "Bot token is required\n"
                "  Set DISCORD_BOT_TOKEN environment variable or add 'token' to config.json"
            )
        elif len(self.token) < MIN_TOKEN_LENGTH:
            errors.append(
                f"Bot token appears invalid (minimum {MIN_TOKEN_LENGTH} characters)\n"
                f"  Current length: {len(self.token)} characters"
            )
        
        # Validate owner_id
        if not self.owner_id:
            errors.append(
                "Owner ID is required\n"
                "  Set DISCORD_OWNER_ID environment variable or add 'owner_id' to config.json\n"
                "  To find your Discord ID: Enable Developer Mode in Discord settings,\n"
                "  then right-click your username and select 'Copy ID'"
            )
        elif not isinstance(self.owner_id, int):
            errors.append(
                f"Owner ID must be an integer, got {type(self.owner_id).__name__}"
            )
        elif not self._is_valid_snowflake(self.owner_id):
            errors.append(
                f"Owner ID {self.owner_id} is not a valid Discord snowflake ID\n"
                f"  Discord IDs are 17-19 digit numbers"
            )
        
        # Validate music_directory if set
        if self.music_directory:
            music_path = Path(self.music_directory)
            if not music_path.exists():
                warnings.append(
                    f"music_directory does not exist: {self.music_directory}\n"
                    f"  Local file playback will not work until this directory is created"
                )
            elif not music_path.is_dir():
                errors.append(
                    f"music_directory is not a directory: {self.music_directory}"
                )
        
        # Validate limits
        if self.max_queue_size < 1:
            errors.append("max_queue_size must be at least 1")
        elif self.max_queue_size > 1000:
            warnings.append(
                f"max_queue_size is very high ({self.max_queue_size})\n"
                f"  This may cause memory issues"
            )
        
        if self.max_playlist_size < 1:
            errors.append("max_playlist_size must be at least 1")
        elif self.max_playlist_size > 1000:
            warnings.append(
                f"max_playlist_size is very high ({self.max_playlist_size})\n"
                f"  This may cause performance issues"
            )
        
        # Validate file extensions
        if not self.allowed_file_extensions:
            errors.append("allowed_file_extensions cannot be empty")
        
        # Log warnings
        if warnings:
            warning_msg = "Configuration warnings:\n" + "\n".join(f"  - {w}" for w in warnings)
            logger.warning(warning_msg)
        
        # Raise errors if any
        if errors:
            error_msg = (
                "=" * 70 + "\n"
                "CONFIGURATION ERROR\n"
                "=" * 70 + "\n"
                "The following configuration issues must be fixed:\n\n" +
                "\n\n".join(f"{i+1}. {e}" for i, e in enumerate(errors)) +
                "\n\n" + "=" * 70
            )
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        self._validated = True
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
    
    def to_dict(self) -> Dict[str, Any]:
        """
        FIX #2: Convert config to dictionary for service initialization
        FIX CONFIG #3: Include web_dashboard in dict
        
        Returns:
            Dictionary representation of config
        """
        return {
            'token': self.token,
            'owner_id': self.owner_id,
            'playing': self.playing,
            'command_prefix': self.command_prefix,
            'max_queue_size': self.max_queue_size,
            'max_playlist_size': self.max_playlist_size,
            'allowed_file_extensions': self.allowed_file_extensions,
            'music_directory': self.music_directory,
            'llm': self.llm,
            'llm_config': self.llm_config,
            'music_synthesis': self.music_synthesis,
            'web_dashboard': self.web_dashboard
        }
    
    def get_config_template(self) -> str:
        """
        Get a template config.json file content
        FIX CONFIG #3: Match config.example.json EXACTLY
        
        Returns:
            JSON template string
        """
        template = {
            "token": "YOUR_BOT_TOKEN_HERE",
            "owner_id": 123456789012345678,  # FIX: Use number, not string
            "playing": DEFAULT_PLAYING,
            "command_prefix": DEFAULT_PREFIX,
            "max_queue_size": DEFAULT_MAX_QUEUE_SIZE,
            "max_playlist_size": DEFAULT_MAX_PLAYLIST_SIZE,
            "allowed_file_extensions": DEFAULT_ALLOWED_EXTENSIONS,
            "music_directory": None,
            "llm": {
                "enabled": False,
                "provider": "ollama",  # FIX: Use ollama, not openai
                "model": "llama3",     # FIX: Use llama3, not gpt-3.5-turbo
                "api_key": None,
                "base_url": "http://localhost:11434",  # FIX: Add missing field
                "timeout": 30,                          # FIX: Add missing field
                "max_tokens": 500                       # FIX: Add missing field
            },
            "music_synthesis": {
                "enabled": False,
                "backend": "disabled",
                "cache_dir": "generated_music",              # FIX: Add missing field
                "max_cache_size_mb": 1000,                   # FIX: Add missing field
                "default_duration": 30,                      # FIX: Add missing field
                "default_quality": "medium",                 # FIX: Add missing field
                "suno_api_key": None,                        # FIX: Add missing field
                "suno_api_url": "https://api.suno.ai/v1",   # FIX: Add missing field
                "musicgen_model": "facebook/musicgen-small"  # FIX: Add missing field
            },
            "web_dashboard": {  # FIX: Add completely missing section
                "enabled": True,
                "host": "0.0.0.0",
                "port": 8000
            }
        }
        return json.dumps(template, indent=4)


# FIX #12: Wrap config initialization with helpful error handling
# FIX CONFIG #4: Show project root in error messages
try:
    config = Config()
except ConfigurationError as e:
    # Print error to console before logger is fully set up
    print(f"\n{e}\n")
    print(f"Project root: {get_project_root()}")
    print("\nTo create a config file template, run:")
    print("  python -c \"from core.config import Config; print(Config().get_config_template())\" > config.json")
    print("\nOr set environment variables:")
    print("  export DISCORD_BOT_TOKEN='your_token_here'")
    print("  export DISCORD_OWNER_ID='your_user_id_here'")
    raise SystemExit(1)
except Exception as e:
    print(f"\nUnexpected error loading configuration: {e}\n")
    print(f"Project root: {get_project_root()}")
    raise SystemExit(1)
