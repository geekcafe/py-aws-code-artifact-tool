# AWS CodeArtifact CLI Tool

A command-line interface for building and deploying Python projects to AWS CodeArtifact.

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/geekcafe/py-aws-code-artifact-tool.git
cd py-aws-code-artifact-tool

# Install the package in development mode
pip install -e .
```

### From PyPI (once published)

```bash
pip install py-aws-code-artifact-tool
```

## Usage

The CLI tool provides three main commands:

- `configure`: Set up AWS CodeArtifact credentials
- `build`: Build the Python package
- `publish`: Publish the package to AWS CodeArtifact

### Configuration

Before using the tool, you need to configure your AWS CodeArtifact credentials:

```bash
py-aws-code-artifact configure
```

This will prompt you for:
- CodeArtifact domain
- CodeArtifact repository name
- AWS account number
- AWS profile (optional)
- AWS region (optional)

Credentials are stored in a `.aws-codeartifact.json` file in your project directory and automatically added to `.gitignore`.

### Building a Package

To build your Python package:

```bash
py-aws-code-artifact build
```

This command:
1. Locates your project's `pyproject.toml` file
2. Ensures you're in a virtual environment (or prompts to create one)
3. Extracts version information
4. Builds the package using your local environment

### Publishing a Package

To publish your package to AWS CodeArtifact:

```bash
py-aws-code-artifact publish
```

This command:
1. Authenticates with AWS CodeArtifact
2. Publishes your package to the configured repository

## Requirements

- Python 3.8 or higher
- AWS CLI installed and configured
- A Python project with a valid `pyproject.toml` file

## Development

### Running Tests

```bash
python -m pytest
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
mkdocs build
```
