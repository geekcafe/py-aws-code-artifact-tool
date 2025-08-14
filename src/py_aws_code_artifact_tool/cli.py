#!/usr/bin/env python3
"""
AWS CodeArtifact CLI Tool

A command-line interface for building and deploying Python projects to AWS CodeArtifact.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .main import AWSCodeArtifactsService
from .config import Config


def find_pyproject_toml() -> Optional[Path]:
    """Find the pyproject.toml file in the current directory or parent directories."""
    current_dir = Path.cwd()
    
    # Look in current directory and up to 3 parent directories
    for _ in range(4):
        pyproject_path = current_dir / "pyproject.toml"
        if pyproject_path.exists():
            return pyproject_path
        
        # Move up one directory
        parent_dir = current_dir.parent
        if parent_dir == current_dir:  # Reached root directory
            break
        current_dir = parent_dir
    
    return None


def ensure_virtual_env() -> bool:
    """
    Check if a virtual environment exists and is activated.
    If not, prompt the user to create one.
    
    Returns:
        bool: True if virtual environment is active, False otherwise
    """
    # Check if we're in a virtual environment
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    
    if not in_venv:
        print("No active virtual environment detected.")
        create_venv = input("Would you like to create a virtual environment? (y/n): ")
        
        if create_venv.lower() == 'y':
            venv_name = input("Enter virtual environment name (default: .venv): ") or ".venv"
            
            import subprocess
            try:
                print(f"Creating virtual environment '{venv_name}'...")
                subprocess.run([sys.executable, "-m", "venv", venv_name], check=True)
                
                # Provide activation instructions
                if os.name == 'nt':  # Windows
                    activate_cmd = f"{venv_name}\\Scripts\\activate"
                else:  # Unix/Linux/Mac
                    activate_cmd = f"source {venv_name}/bin/activate"
                
                print(f"\nVirtual environment created successfully!")
                print(f"To activate it, run:\n  {activate_cmd}")
                print("Then run this command again.")
                return False
            except subprocess.CalledProcessError:
                print("Failed to create virtual environment.")
                return False
        else:
            print("A virtual environment is recommended for building Python packages.")
            proceed = input("Do you want to proceed anyway? (y/n): ")
            return proceed.lower() == 'y'
    
    return True


def save_credentials(config_data: Dict[str, Any], project_dir: Path) -> None:
    """
    Save AWS CodeArtifact credentials to a local .json file.
    
    Args:
        config_data: Dictionary containing AWS CodeArtifact credentials
        project_dir: Project directory path
    """
    config_file = project_dir / ".aws-codeartifact.json"
    
    # Create .gitignore entry if it doesn't exist
    gitignore_path = project_dir / ".gitignore"
    gitignore_entry = ".aws-codeartifact.json"
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        if gitignore_entry not in gitignore_content:
            with open(gitignore_path, 'a') as f:
                if not gitignore_content.endswith('\n'):
                    f.write('\n')
                f.write(f"{gitignore_entry}\n")
                print(f"Added {gitignore_entry} to .gitignore")
    else:
        with open(gitignore_path, 'w') as f:
            f.write(f"{gitignore_entry}\n")
            print(f"Created .gitignore with {gitignore_entry}")
    
    # Save credentials
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"AWS CodeArtifact credentials saved to {config_file}")


def build_command(args):
    """Build the Python package."""
    pyproject_path = find_pyproject_toml()
    
    if not pyproject_path:
        print("Error: No pyproject.toml found in the current directory or parent directories.")
        sys.exit(1)
    
    project_dir = pyproject_path.parent
    
    if not ensure_virtual_env():
        sys.exit(1)
    
    # Load or create config
    config = Config(project_dir)
    
    if not config.is_configured():
        print("AWS CodeArtifact credentials not configured.")
        configure_command(args)
    
    # Set environment variables from config
    config.set_environment_variables()
    
    # Build the package
    service = AWSCodeArtifactsService()
    service.build()
    
    print("Build completed successfully.")


def publish_command(args):
    """Publish the Python package to AWS CodeArtifact."""
    pyproject_path = find_pyproject_toml()
    
    if not pyproject_path:
        print("Error: No pyproject.toml found in the current directory or parent directories.")
        sys.exit(1)
    
    project_dir = pyproject_path.parent
    
    # Load config
    config = Config(project_dir)
    
    if not config.is_configured():
        print("AWS CodeArtifact credentials not configured.")
        configure_command(args)
    
    # Set environment variables from config
    config.set_environment_variables()
    
    # Publish the package
    service = AWSCodeArtifactsService()
    service.publish()
    
    print("Package published successfully to AWS CodeArtifact.")


def configure_command(args):
    """Configure AWS CodeArtifact credentials."""
    pyproject_path = find_pyproject_toml()
    
    if not pyproject_path:
        print("Error: No pyproject.toml found in the current directory or parent directories.")
        sys.exit(1)
    
    project_dir = pyproject_path.parent
    
    # Prompt for AWS CodeArtifact credentials
    print("AWS CodeArtifact Configuration")
    print("=============================")
    
    domain = input("Enter CodeArtifact domain: ")
    repository = input("Enter CodeArtifact repository name: ")
    account = input("Enter AWS account number: ")
    profile = input("Enter AWS profile (leave empty for default): ") or None
    region = input("Enter AWS region (leave empty for default): ") or None
    
    # Create config data
    config_data = {
        "domain": domain,
        "repository": repository,
        "account": account,
        "profile": profile,
        "region": region
    }
    
    # Save credentials
    save_credentials(config_data, project_dir)
    
    print("Configuration completed successfully.")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="AWS CodeArtifact CLI Tool for Python projects"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Build the Python package")
    
    # Publish command
    publish_parser = subparsers.add_parser("publish", help="Publish the Python package to AWS CodeArtifact")
    
    # Configure command
    configure_parser = subparsers.add_parser("configure", help="Configure AWS CodeArtifact credentials")
    
    args = parser.parse_args()
    
    if args.command == "build":
        build_command(args)
    elif args.command == "publish":
        publish_command(args)
    elif args.command == "configure":
        configure_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
