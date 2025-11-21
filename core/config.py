"""
Configuration management with security enhancements
"""
import json
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger('discord_bot')


class Config:
    """Bot configuration with validation and security features"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = config_path
        self.token: str = ""
        self.owner_id: int = 0
        self.playing: str = "!help for commands"
        self.command_prefix: str = "!"
        
        # Security settings
        self.max_queue_size: int = 100
        self.max_playlist_size: int = 500
        self.allowed_file_extensions: list = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.opus']
        self.music_directory: Optional[str] = None
        
        self.load()
    
    def load(self) -> None:
        """Load configuration from file or environment variables"""
        # Try environment variables first (more secure)
        self.token = os.getenv('DISCORD_BOT_TOKEN', '')
        owner_id_env = os.getenv('DISCORD_OWNER_ID', '')
        self.playing = os.getenv('DISCORD_PLAYING', '!help for commands')
        self.command_prefix = os.getenv('DISCORD_PREFIX', '!')
        
        # If environment variables not set, try config file
        if not self.token and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    self.token = data.get('token', '')
                    
                    # Convert owner_id to int if it's a string
                    owner_id_raw = data.get('owner_id', 0)
                    if isinstance(owner_id_raw, str):
                        try:
                            self.owner_id = int(owner_id_raw)
                        except ValueError:
                            logger.error(f"Invalid owner_id in config.json: {owner_id_raw}")
                            self.owner_id = 0
                    else:
                        self.owner_id = owner_id_raw
                    
                    self.playing = data.get('playing', '!help for commands')
                    self.command_prefix = data.get('command_prefix', '!')
                    
                    # Load security settings
                    self.max_queue_size = data.get('max_queue_size', 100)
                    self.max_playlist_size = data.get('max_playlist_size', 500)
                    self.allowed_file_extensions = data.get('allowed_file_extensions', 
                                                            ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.opus'])
                    self.music_directory = data.get('music_directory')
                    
                    logger.info(f"Configuration loaded from {self.config_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse config file: {e}")
                raise
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                raise
        elif owner_id_env:
            # Use environment variable for owner_id
            try:
                self.owner_id = int(owner_id_env)
            except ValueError:
                logger.error(f"Invalid DISCORD_OWNER_ID: {owner_id_env}")
                raise
        
        # Validate configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate configuration with security checks"""
        errors = []
        
        # Validate token
        if not self.token:
            errors.append("Bot token is required (set DISCORD_BOT_TOKEN or add to config.json)")
        elif len(self.token) < 50:
            errors.append("Bot token appears invalid (too short)")
        
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
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validated successfully")
    
    def _is_valid_snowflake(self, snowflake_id: int) -> bool:
        """Validate Discord snowflake ID (17-19 digits)"""
        return 10**16 <= snowflake_id < 10**19
    
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
