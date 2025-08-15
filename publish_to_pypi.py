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


def check_authentication(repository="pypi", config_file=None):
    """Check if the user is authenticated with PyPI or TestPyPI."""
    cmd = [sys.executable, "-m", "twine", "check", "--strict", "README.md"]
    
    env = os.environ.copy()
    
    # If using a config file, set TWINE_CONFIG_FILE
    if config_file:
        env["TWINE_CONFIG_FILE"] = config_file
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, env=env)
        return True
    except subprocess.CalledProcessError:
        return False


def show_auth_instructions(repository="pypi", config_file=None):
    """Show authentication instructions for PyPI or TestPyPI."""
    print_header("Authentication Required")
    
    repo_name = "TestPyPI" if repository == "testpypi" else "PyPI"
    repo_url = "https://test.pypi.org" if repository == "testpypi" else "https://pypi.org"
    
    print_error(f"You are not authenticated with {repo_name}.")
    print_info("To authenticate, you need to:")
    print("\n1. Create an API token:")
    print(f"   - Go to {repo_url}/manage/account/")
    print("   - Navigate to 'API tokens' and create a new token")
    print("   - Select 'Entire account (all projects)' scope")
    
    if config_file:
        print("\n2. Add your credentials to your local .pypirc file:")
        print(f"   - Edit {config_file}")
        print("   - Ensure it contains:")
        if repository == "testpypi":
            print("     [testpypi]")
            print("     username = __token__")
            print("     password = pypi-YOUR-TOKEN-HERE")
        else:
            print("     [pypi]")
            print("     username = __token__")
            print("     password = pypi-YOUR-TOKEN-HERE")
    else:
        print("\n2. Set up your credentials:")
        print("   - Create a ~/.pypirc file with:")
        print("     [distutils]")
        print("     index-servers =")
        print("         pypi")
        print("         testpypi")
        print("")
        if repository == "testpypi":
            print("     [testpypi]")
            print("     repository = https://test.pypi.org/legacy/")
            print("     username = __token__")
            print("     password = pypi-YOUR-TOKEN-HERE")
        else:
            print("     [pypi]")
            print("     username = __token__")
            print("     password = pypi-YOUR-TOKEN-HERE")
        
        print("\n   - OR set environment variables:")
        print("     export TWINE_USERNAME=__token__")
        print("     export TWINE_PASSWORD=pypi-YOUR-TOKEN-HERE")
    
    print("\nReplace 'pypi-YOUR-TOKEN-HERE' with your actual token.")
    print_info("\nFor more information, visit: https://twine.readthedocs.io/en/latest/#configuration")
    
    sys.exit(1)


def get_current_version():
    """Get the current version from pyproject.toml."""
    try:
        import toml
        with open("pyproject.toml", "r") as f:
            data = toml.load(f)
            return data.get("project", {}).get("version")
    except (ImportError, FileNotFoundError, KeyError):
        return None


def show_version_conflict_help():
    """Show help for version conflict errors."""
    print_header("Version Conflict Error")
    
    current_version = get_current_version()
    version_info = f"Current version: {current_version}" if current_version else ""
    
    print_error("The package version already exists on PyPI.")
    print_info("To resolve this issue:")
    print("\n1. Update the version number in pyproject.toml")
    if version_info:
        print(f"   {version_info} → increment to a new version")
    print("\n2. Rebuild the package:")
    print("   python -m build")
    print("\n3. Run this publish script again")
    
    print_info("\nVersion numbering follows Semantic Versioning (SemVer):")
    print("MAJOR.MINOR.PATCH (e.g., 1.2.3)")
    print("- MAJOR: incompatible API changes")
    print("- MINOR: add functionality (backwards compatible)")
    print("- PATCH: bug fixes (backwards compatible)")
    
    sys.exit(1)


def handle_upload_error(error_output):
    """Handle common upload errors with helpful messages."""
    # Check for version conflict
    if "File already exists" in error_output:
        show_version_conflict_help()
    
    # Check for invalid classifiers
    elif "invalid classifier" in error_output.lower():
        print_header("Invalid Classifier Error")
        print_error("Your package has invalid classifiers in pyproject.toml.")
        print_info("Please check your classifiers against the list at:")
        print("https://pypi.org/classifiers/")
        sys.exit(1)
    
    # Check for missing required metadata
    elif "required metadata" in error_output.lower():
        print_header("Missing Metadata Error")
        print_error("Your package is missing required metadata.")
        print_info("Check your pyproject.toml for required fields:")
        print("- name\n- version\n- description\n- author\n- author_email")
        sys.exit(1)
    
    # Generic error
    else:
        print_header("Upload Error")
        print_error("Failed to upload package.")
        print_info("Error details:")
        print(error_output)
        sys.exit(1)


def upload_to_pypi(repository, config_file=None):
    """Upload the package to PyPI or TestPyPI."""
    print_header(f"Uploading to {'TestPyPI' if repository == 'testpypi' else 'PyPI'}")
    
    # Check authentication before attempting upload
    if not check_authentication(repository, config_file):
        show_auth_instructions(repository, config_file)
    
    cmd = [sys.executable, "-m", "twine", "upload"]
    
    if repository == "testpypi":
        cmd.extend(["--repository", "testpypi"])
    
    if config_file:
        cmd.extend(["--config-file", config_file])
    
    cmd.append("dist/*")
    
    cmd_str = " ".join(cmd)
    print_info(f"Running: {cmd_str}")
    
    try:
        # Use shell=True to properly handle the glob pattern but capture output for error analysis
        result = subprocess.run(cmd_str, shell=True, check=True, capture_output=True, text=True)
        print_success("Package uploaded successfully!")
    except subprocess.CalledProcessError as e:
        # Handle the error with detailed feedback
        error_output = e.stderr or e.stdout or "Unknown error occurred"
        handle_upload_error(error_output)
        
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
            return data.get("project", {}).get("name", "py-aws-code-artifact-tool")
    except (ImportError, FileNotFoundError):
        return "py-aws-code-artifact-tool"


def main():
    """Main function."""
    print_header("PyPI Publishing Script")
    
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
        if not check_authentication():
            print_warning("You are not authenticated with PyPI.")
            print_info("The upload will likely fail without proper authentication.")
            
            proceed = input("Do you want to proceed anyway? (y/n): ")
            if proceed.lower() != 'y':
                show_auth_instructions()
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
