"""
Configuration management module
Handles loading and validation of configuration
"""
import json
import os
from typing import Dict, Any

class ConfigManager:
    """Manages bot configuration"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                "Please create config.json with your bot token and settings"
            )
        
        with open(self.config_path, 'r') as f:
            self._config = json.load(f)
        
        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration fields"""
        required_fields = ['token', 'owner_id']
        missing_fields = [field for field in required_fields if field not in self._config]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}"
            )
        
        if self._config['token'] == 'YOUR_BOT_TOKEN_HERE':
            raise ValueError("Please set your bot token in config.json")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access"""
        return self._config[key]

# Global configuration instance
config = ConfigManager()