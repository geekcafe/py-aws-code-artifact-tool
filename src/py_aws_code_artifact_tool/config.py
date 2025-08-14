"""
Configuration module for AWS CodeArtifact credentials.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """
    Configuration class for AWS CodeArtifact credentials.
    Handles loading, saving, and providing environment variables.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize the configuration.
        
        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = project_dir
        self.config_file = project_dir / ".aws-codeartifact.json"
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the config file.
        
        Returns:
            Dict containing configuration data or empty dict if file doesn't exist
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.config_file}. Using default configuration.")
                return {}
        return {}
    
    def save_config(self, config_data: Dict[str, Any]) -> None:
        """
        Save configuration to the config file.
        
        Args:
            config_data: Dictionary containing configuration data
        """
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def is_configured(self) -> bool:
        """
        Check if AWS CodeArtifact is configured.
        
        Returns:
            bool: True if configured, False otherwise
        """
        required_keys = ["domain", "repository", "account"]
        return all(key in self.config_data for key in required_keys)
    
    def set_environment_variables(self) -> None:
        """
        Set environment variables from the configuration.
        """
        if not self.is_configured():
            return
        
        # Set environment variables
        os.environ["CODEARTIFACT_DOMAIN"] = self.config_data["domain"]
        os.environ["CODEARTIFACT_REPOSITORY_NAME"] = self.config_data["repository"]
        os.environ["CODEARTIFACT_AWS_ACCCOUNT_NUMBER"] = self.config_data["account"]
        
        if "profile" in self.config_data and self.config_data["profile"]:
            os.environ["CODEARTIFACT_REPOSITORY_PROFILE"] = self.config_data["profile"]
        
        if "region" in self.config_data and self.config_data["region"]:
            os.environ["CODEARTIFACT_REPOSITORY_REGION"] = self.config_data["region"]
    
    def get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return self.config_data.get(key, default)
