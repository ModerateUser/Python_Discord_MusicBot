"""
Configuration management module
Handles loading and validation of configuration with security best practices
"""
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class ConfigManager:
    """Manages bot configuration with security validation"""
    
    # Security defaults
    DEFAULT_MAX_QUEUE_SIZE = 100
    DEFAULT_MAX_PLAYLIST_SIZE = 500
    DEFAULT_ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.opus']
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from file with environment variable override support"""
        # Check for environment variables first (higher priority)
        token_from_env = os.getenv('DISCORD_BOT_TOKEN')
        owner_id_from_env = os.getenv('DISCORD_OWNER_ID')
        
        if not os.path.exists(self.config_path):
            # If no config file but env vars exist, use them
            if token_from_env and owner_id_from_env:
                self._config = {
                    'token': token_from_env,
                    'owner_id': int(owner_id_from_env),
                    'playing': os.getenv('DISCORD_PLAYING', '!help for commands'),
                    'command_prefix': os.getenv('DISCORD_PREFIX', '!'),
                }
                self._apply_defaults()
                self._validate()
                return
            
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                "Please create config.json from config.example.json or set environment variables:\n"
                "  DISCORD_BOT_TOKEN=your_token\n"
                "  DISCORD_OWNER_ID=your_user_id"
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")
        
        # Environment variables override config file
        if token_from_env:
            self._config['token'] = token_from_env
        if owner_id_from_env:
            self._config['owner_id'] = int(owner_id_from_env)
        
        self._apply_defaults()
        self._validate()
    
    def _apply_defaults(self) -> None:
        """Apply default values for optional configuration"""
        self._config.setdefault('command_prefix', '!')
        self._config.setdefault('playing', '!help for commands')
        self._config.setdefault('max_queue_size', self.DEFAULT_MAX_QUEUE_SIZE)
        self._config.setdefault('max_playlist_size', self.DEFAULT_MAX_PLAYLIST_SIZE)
        self._config.setdefault('allowed_file_extensions', self.DEFAULT_ALLOWED_EXTENSIONS)
        self._config.setdefault('music_directory', None)
    
    def _validate(self) -> None:
        """Validate required configuration fields with security checks"""
        required_fields = ['token', 'owner_id']
        missing_fields = [field for field in required_fields if field not in self._config]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}\n"
                "Required: token, owner_id"
            )
        
        # Validate token
        token = self._config['token']
        if not isinstance(token, str) or not token.strip():
            raise ValueError("Bot token must be a non-empty string")
        
        if token in ['YOUR_BOT_TOKEN_HERE', 'your_token_here', 'token']:
            raise ValueError(
                "Please set a valid bot token in config.json or DISCORD_BOT_TOKEN environment variable"
            )
        
        # Basic token format validation (Discord bot tokens are typically 59+ chars)
        if len(token) < 50:
            raise ValueError(
                "Bot token appears invalid (too short). "
                "Discord bot tokens are typically 59+ characters."
            )
        
        # Validate owner_id
        owner_id = self._config['owner_id']
        if not isinstance(owner_id, int):
            try:
                self._config['owner_id'] = int(owner_id)
            except (ValueError, TypeError):
                raise ValueError(
                    f"owner_id must be an integer (Discord user ID), got: {type(owner_id).__name__}"
                )
        
        # Validate owner_id is a valid Discord snowflake (17-19 digits)
        if not (10**16 <= self._config['owner_id'] <= 10**19):
            raise ValueError(
                f"owner_id appears invalid: {self._config['owner_id']}. "
                "Discord user IDs are typically 17-19 digits."
            )
        
        # Validate security limits
        max_queue = self._config.get('max_queue_size', self.DEFAULT_MAX_QUEUE_SIZE)
        if not isinstance(max_queue, int) or max_queue < 1 or max_queue > 1000:
            raise ValueError("max_queue_size must be between 1 and 1000")
        
        max_playlist = self._config.get('max_playlist_size', self.DEFAULT_MAX_PLAYLIST_SIZE)
        if not isinstance(max_playlist, int) or max_playlist < 1 or max_playlist > 5000:
            raise ValueError("max_playlist_size must be between 1 and 5000")
        
        # Validate music_directory if set
        music_dir = self._config.get('music_directory')
        if music_dir is not None:
            music_path = Path(music_dir)
            if not music_path.exists():
                raise ValueError(f"music_directory does not exist: {music_dir}")
            if not music_path.is_dir():
                raise ValueError(f"music_directory is not a directory: {music_dir}")
            # Store as absolute path for security
            self._config['music_directory'] = str(music_path.resolve())
        
        # Validate allowed extensions
        allowed_ext = self._config.get('allowed_file_extensions', [])
        if not isinstance(allowed_ext, list):
            raise ValueError("allowed_file_extensions must be a list")
        
        # Ensure all extensions start with a dot
        self._config['allowed_file_extensions'] = [
            ext if ext.startswith('.') else f'.{ext}'
            for ext in allowed_ext
        ]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access"""
        return self._config[key]
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is the bot owner (type-safe comparison)"""
        return int(user_id) == int(self._config['owner_id'])
    
    def is_file_allowed(self, filepath: str) -> bool:
        """
        Check if a file is allowed to be played based on security settings
        
        Security checks:
        1. File extension must be in allowed list
        2. If music_directory is set, file must be within that directory
        3. Path must not contain directory traversal attempts
        """
        file_path = Path(filepath)
        
        # Check for directory traversal attempts
        try:
            resolved_path = file_path.resolve()
        except (OSError, RuntimeError):
            return False
        
        # Check file extension
        if file_path.suffix.lower() not in self._config['allowed_file_extensions']:
            return False
        
        # If music_directory is set, enforce it
        music_dir = self._config.get('music_directory')
        if music_dir:
            music_path = Path(music_dir).resolve()
            try:
                # Check if file is within music directory
                resolved_path.relative_to(music_path)
            except ValueError:
                # File is outside music directory
                return False
        
        return True


# Global configuration instance
config = ConfigManager()
