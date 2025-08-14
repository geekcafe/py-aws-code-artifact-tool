#!/usr/bin/env bash
set -euo pipefail

# ANSI color codes
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"
RESET="\033[0m"

# Print functions
print_header() {
  echo -e "\n${CYAN}=================================================${RESET}"
  echo -e "${CYAN}  $1${RESET}"
  echo -e "${CYAN}=================================================${RESET}"
}

print_success() {
  echo -e "${GREEN}✅ $1${RESET}"
}

print_error() {
  echo -e "${RED}❌ $1${RESET}"
}

print_info() {
  echo -e "${BLUE}ℹ️ $1${RESET}"
}

print_warning() {
  echo -e "${YELLOW}⚠️ $1${RESET}"
}

# Check dependencies
check_dependencies() {
  print_info "Checking dependencies..."
  
  if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed."
    exit 1
  fi
  
  if ! python3 -c "import build" &> /dev/null; then
    print_warning "Python build package not found. Installing..."
    python3 -m pip install build
  fi
  
  if ! python3 -c "import twine" &> /dev/null; then
    print_warning "Twine package not found. Installing..."
    python3 -m pip install twine
  fi
  
  print_success "All dependencies are installed."
}

# Clean dist directory
clean_dist() {
  print_info "Cleaning dist directory..."
  rm -rf dist
  mkdir -p dist
  print_success "Dist directory cleaned."
}

# Build package
build_package() {
  print_header "Building Package"
  python3 -m build
  if [ $? -ne 0 ]; then
    print_error "Failed to build package."
    exit 1
  fi
  print_success "Package built successfully!"
}

# Get package name from pyproject.toml
get_package_name() {
  if command -v python3 &> /dev/null && python3 -c "import toml" &> /dev/null; then
    PACKAGE_NAME=$(python3 -c "import toml; print(toml.load('pyproject.toml').get('project', {}).get('name', 'py-aws-code-artifact-tool'))")
  else
    PACKAGE_NAME="py-aws-code-artifact-tool"
  fi
  echo "$PACKAGE_NAME"
}

# Upload to PyPI or TestPyPI
upload_to_pypi() {
  local repo="$1"
  local pypirc_path="$2"
  local repo_flag=""
  local repo_name="PyPI"
  local config_flag=""
  
  if [ "$repo" == "testpypi" ]; then
    repo_flag="--repository testpypi"
    repo_name="TestPyPI"
  fi
  
  if [ -n "$pypirc_path" ]; then
    config_flag="--config-file $pypirc_path"
  fi
  
  print_header "Uploading to $repo_name"
  
  python3 -m twine upload $repo_flag $config_flag dist/*
  if [ $? -ne 0 ]; then
    print_error "Failed to upload package to $repo_name."
    exit 1
  fi
  
  print_success "Package uploaded successfully to $repo_name!"
  
  local package_name=$(get_package_name)
  
  if [ "$repo" == "testpypi" ]; then
    print_info "To install from TestPyPI, run:"
    echo "pip install --index-url https://test.pypi.org/simple/ $package_name"
  else
    print_info "To install from PyPI, run:"
    echo "pip install $package_name"
  fi
}

# Main function
main() {
  print_header "PyPI Publishing Script"
  
  check_dependencies
  
  # Check for local .pypirc file
  local pypirc_path=""
  if [ -f "./.pypirc" ]; then
    print_info "Found local .pypirc file in project directory."
    read -p "Do you want to use this local .pypirc file? (y/n): " use_local_pypirc
    if [[ "$use_local_pypirc" =~ ^[Yy]$ ]]; then
      pypirc_path="$(pwd)/.pypirc"
      print_success "Using local .pypirc file: $pypirc_path"
    fi
  else
    print_info "No local .pypirc file found. You can create one in the project directory."
    read -p "Do you want to create a local .pypirc file now? (y/n): " create_pypirc
    if [[ "$create_pypirc" =~ ^[Yy]$ ]]; then
      create_local_pypirc
      pypirc_path="$(pwd)/.pypirc"
    fi
  fi
  
  # Check if user is authenticated
  if [ -z "$pypirc_path" ] && ! python3 -m twine check --strict README.md &> /dev/null; then
    print_warning "You might not be authenticated with PyPI."
    print_info "Please make sure you have a ~/.pypirc file or environment variables set."
    print_info "For more information, visit: https://twine.readthedocs.io/en/latest/#configuration"
    
    read -p "Do you want to proceed anyway? (y/n): " proceed
    if [[ ! "$proceed" =~ ^[Yy]$ ]]; then
      exit 0
    fi
  fi
  
  # Prompt for repository
  print_info "Where do you want to publish the package?"
  echo "1. TestPyPI (recommended for testing)"
  echo "2. PyPI (public package index)"
  
  read -p "Enter your choice (1/2): " choice
  
  if [ "$choice" == "1" ]; then
    repository="testpypi"
  else
    repository="pypi"
    
    print_warning "You are about to publish to the public PyPI repository."
    read -p "Are you sure you want to proceed? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
      print_info "Operation cancelled."
      exit 0
    fi
  fi
  
  # Clean dist directory
  clean_dist
  
  # Build package
  build_package
  
  # Upload to PyPI
  upload_to_pypi "$repository" "$pypirc_path"
}

# Create a local .pypirc file
create_local_pypirc() {
  print_header "Creating Local .pypirc File"
  
  cat > ./.pypirc << EOF
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
EOF

  print_info "Created .pypirc template in the project directory."
  print_info "Please edit the file and add your API tokens for PyPI and TestPyPI."
  print_info "You can generate tokens at https://pypi.org/manage/account/ and https://test.pypi.org/manage/account/"
  
  # Add to .gitignore if it exists
  if [ -f ".gitignore" ]; then
    if ! grep -q ".pypirc" ".gitignore"; then
      echo ".pypirc" >> ".gitignore"
      print_info "Added .pypirc to .gitignore"
    fi
  else
    echo ".pypirc" > ".gitignore"
    print_info "Created .gitignore with .pypirc entry"
  fi
  
  # Open the file in an editor if possible
  if command -v nano &> /dev/null; then
    read -p "Do you want to edit the .pypirc file now with nano? (y/n): " edit_now
    if [[ "$edit_now" =~ ^[Yy]$ ]]; then
      nano ./.pypirc
    fi
  else
    print_info "Please edit ./.pypirc manually to add your tokens."
    read -p "Press Enter when you've edited the file..." 
  fi
}

# Run main function
main
