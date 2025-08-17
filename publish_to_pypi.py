#!/usr/bin/env python3
"""
PyPI Publishing Script

This script builds and publishes the package to PyPI or TestPyPI.
It prompts for the target repository and handles the build and upload process.
"""
import os
import shutil
import subprocess
import sys
import hashlib
import urllib.request
import time
import socket
from pathlib import Path


def print_colored(message, color_code):
    """Print colored text to the console."""
    print(f"\033[{color_code}m{message}\033[0m")


def print_success(message):
    """Print success message in green."""
    print_colored(f"✅ {message}", "92")


def print_error(message):
    """Print error message in red."""
    print_colored(f"❌ {message}", "91")


def print_info(message):
    """Print info message in blue."""
    print_colored(f"ℹ️ {message}", "94")


def print_warning(message):
    """Print warning message in yellow."""
    print_colored(f"⚠️ {message}", "93")


def print_header(message):
    """Print header message."""
    print("\n" + "=" * 60)
    print_colored(f"  {message}", "96")
    print("=" * 60)


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import build
        import twine
        return True
    except ImportError as e:
        print_error(f"Missing required dependency: {e.name}")
        print_info("Installing required dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "build", "twine"], check=True)
            return True
        except subprocess.CalledProcessError:
            print_error("Failed to install dependencies. Please install them manually:")
            print("pip install build twine")
            return False


def clean_dist_directory():
    """Clean the dist directory."""
    dist_dir = Path("dist")
    if dist_dir.exists():
        print_info("Cleaning dist directory...")
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(exist_ok=True)


def build_package():
    """Build the package."""
    print_header("Building Package")
    try:
        subprocess.run([sys.executable, "-m", "build"], check=True)
        print_success("Package built successfully!")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to build package.")
        return False


def create_local_pypirc():
    """Create a local .pypirc file in the project directory."""
    print_header("Creating Local .pypirc File")
    
    pypirc_content = """\
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = 

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = 
"""
    
    with open(".pypirc", "w") as f:
        f.write(pypirc_content)
    
    print_info("Created .pypirc template in the project directory.")
    print_info("Please edit the file and add your API tokens for PyPI and TestPyPI.")
    print_info("You can generate tokens at https://pypi.org/manage/account/ and https://test.pypi.org/manage/account/")
    
    # Add to .gitignore if it exists
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            gitignore_content = f.read()
        
        if ".pypirc" not in gitignore_content:
            with open(gitignore_path, "a") as f:
                if not gitignore_content.endswith("\n"):
                    f.write("\n")
                f.write(".pypirc\n")
            print_info("Added .pypirc to .gitignore")
    else:
        with open(gitignore_path, "w") as f:
            f.write(".pypirc\n")
        print_info("Created .gitignore with .pypirc entry")
    
    # Try to open the file in an editor
    try:
        if sys.platform == "win32":
            os.startfile(".pypirc")
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", ".pypirc"])
        else:  # Linux
            subprocess.run(["xdg-open", ".pypirc"])
    except:
        print_info("Please edit ./.pypirc manually to add your tokens.")
        input("Press Enter when you've edited the file...")


def upload_to_pypi(repository, config_file=None):
    """Upload the package to PyPI or TestPyPI."""
    print_header(f"Uploading to {'TestPyPI' if repository == 'testpypi' else 'PyPI'}")
    
    cmd = [sys.executable, "-m", "twine", "upload"]
    
    if repository == "testpypi":
        cmd.extend(["--repository", "testpypi"])
    
    if config_file:
        cmd.extend(["--config-file", config_file])
    
    cmd.append("dist/*")
    
    cmd_str = " ".join(cmd)
    print_info(f"Running: {cmd_str}")
    
    try:
        # Use shell=True to properly handle the glob pattern
        subprocess.run(cmd_str, shell=True, check=True)
        
        print_success("Package uploaded successfully!")
        
        if repository == "testpypi":
            package_name = get_package_name()
            print_info(f"\nTo install from TestPyPI, run:")
            print(f"pip install --index-url https://test.pypi.org/simple/ {package_name}")
        else:
            package_name = get_package_name()
            print_info(f"\nTo install from PyPI, run:")
            print(f"pip install {package_name}")
            
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to upload package.")
        return False


def get_package_name():
    """Get the package name from pyproject.toml."""
    try:
        import toml
        with open("pyproject.toml", "r") as f:
            data = toml.load(f)
            return data.get("project", {}).get("name", None)
    except (ImportError, FileNotFoundError):
        print_error("Failed to get package name from pyproject.toml.")
        exit(1)


def fetch_url_with_retry(url, max_retries=3, retry_delay=2):
    """Fetch URL content with retry logic."""
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return response.read()
        except (urllib.error.URLError, socket.timeout) as e:
            if attempt < max_retries - 1:
                print_warning(f"Network error: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise Exception(f"Failed to fetch {url} after {max_retries} attempts: {e}")


def check_for_script_updates():
    """Check if there are updates available for the scripts."""
    # Skip update check in CI mode or if disabled via environment variable
    if "--ci" in sys.argv or os.environ.get("PYPI_SKIP_UPDATE_CHECK", "").lower() in ("1", "true", "yes"):
        print_info("CI mode or PYPI_SKIP_UPDATE_CHECK detected - skipping update check")
        return
        
    print_header("Checking for Script Updates")
    
    # URLs for the scripts
    py_url = "https://raw.githubusercontent.com/geekcafe/publish-to-pypi-scripts/refs/heads/main/publish_to_pypi.py"
    sh_url = "https://raw.githubusercontent.com/geekcafe/publish-to-pypi-scripts/refs/heads/main/publish_to_pypi.sh"
    
    updates_available = False
    
    # Check Python script
    if Path("publish_to_pypi.py").exists():
        try:
            # Get local file hash
            with open("publish_to_pypi.py", "rb") as f:
                local_py_hash = hashlib.md5(f.read()).hexdigest()
            
            # Get remote file hash with retry logic
            remote_py_content = fetch_url_with_retry(py_url)
            remote_py_hash = hashlib.md5(remote_py_content).hexdigest()
            
            if local_py_hash != remote_py_hash:
                print_warning("A new version of publish_to_pypi.py is available.")
                updates_available = True
        except Exception as e:
            print_warning(f"Could not check for Python script updates: {e}")
    
    # Check Shell script
    if Path("publish_to_pypi.sh").exists():
        try:
            # Get local file hash
            with open("publish_to_pypi.sh", "rb") as f:
                local_sh_hash = hashlib.md5(f.read()).hexdigest()
            
            # Get remote file hash with retry logic
            remote_sh_content = fetch_url_with_retry(sh_url)
            remote_sh_hash = hashlib.md5(remote_sh_content).hexdigest()
            
            if local_sh_hash != remote_sh_hash:
                print_warning("A new version of publish_to_pypi.sh is available.")
                updates_available = True
        except Exception as e:
            print_warning(f"Could not check for Shell script updates: {e}")
    
    if updates_available:
        print_info("Updates are available for one or more scripts.")
        update = input("Do you want to update the scripts now? (y/n): ")
        if update.lower() == 'y':
            print_info("Please run the shell script again to update the scripts.")
            print_info("Run: ./publish_to_pypi.sh --update")
            sys.exit(0)
        else:
            print_info("Continuing with current versions...")
    else:
        print_success("All scripts are up to date.")


def main():
    """Main function."""
    print_header("PyPI Publishing Script")
    
    # Check for script updates
    check_for_script_updates()
    
    if not check_dependencies():
        sys.exit(1)
    
    # Check for local .pypirc file
    pypirc_path = None
    local_pypirc = Path(".pypirc")
    
    if local_pypirc.exists():
        print_info("Found local .pypirc file in project directory.")
        use_local = input("Do you want to use this local .pypirc file? (y/n): ")
        if use_local.lower() == 'y':
            pypirc_path = str(local_pypirc.absolute())
            print_success(f"Using local .pypirc file: {pypirc_path}")
    else:
        print_info("No local .pypirc file found. You can create one in the project directory.")
        create_new = input("Do you want to create a local .pypirc file now? (y/n): ")
        if create_new.lower() == 'y':
            create_local_pypirc()
            pypirc_path = str(local_pypirc.absolute())
    
    # Check if user is authenticated (only if not using local .pypirc)
    if not pypirc_path:
        try:
            subprocess.run([sys.executable, "-m", "twine", "check", "--strict", "README.md"], 
                          check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print_warning("You might not be authenticated with PyPI.")
            print_info("Please make sure you have a ~/.pypirc file or environment variables set.")
            print_info("For more information, visit: https://twine.readthedocs.io/en/latest/#configuration")
            
            proceed = input("Do you want to proceed anyway? (y/n): ")
            if proceed.lower() != 'y':
                sys.exit(0)
    
    # Prompt for repository
    print_info("\nWhere do you want to publish the package?")
    print("1. TestPyPI (recommended for testing)")
    print("2. PyPI (public package index)")
    
    choice = input("\nEnter your choice (1/2): ")
    
    repository = "testpypi" if choice == "1" else "pypi"
    
    if repository == "pypi":
        print_warning("\nYou are about to publish to the public PyPI repository.")
        confirm = input("Are you sure you want to proceed? (y/n): ")
        if confirm.lower() != 'y':
            print_info("Operation cancelled.")
            sys.exit(0)
    
    # Clean dist directory
    clean_dist_directory()
    
    # Build package
    if not build_package():
        sys.exit(1)
    
    # Upload to PyPI
    if not upload_to_pypi(repository, pypirc_path):
        sys.exit(1)


if __name__ == "__main__":
    main()
