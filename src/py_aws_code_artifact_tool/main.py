import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

import toml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AWSCodeArtifactsService:
    """AWS CodeArtifacts"""

    def __init__(self) -> None:
        # Get environment variables
        self.domain = os.getenv("CODEARTIFACT_DOMAIN")
        self.repository = os.getenv("CODEARTIFACT_REPOSITORY_NAME")
        self.account = os.getenv("CODEARTIFACT_AWS_ACCCOUNT_NUMBER")
        self.profile = os.getenv("CODEARTIFACT_REPOSITORY_PROFILE")
        self.region = os.getenv("CODEARTIFACT_REPOSITORY_REGION")
        
        # Validate required environment variables
        if not all([self.domain, self.repository, self.account]):
            raise ValueError(
                "Missing required AWS CodeArtifact configuration. "
                "Please run 'py-aws-code-artifact configure' first."
            )

    def build(self):
        """Build the artifacts"""

        # Use current working directory as project root
        project_root = os.getcwd()

        # extract the version
        pyproject_toml = os.path.join(project_root, "pyproject.toml")

        if not os.path.exists(pyproject_toml):
            raise RuntimeError(
                f"The pyproject.toml file ({pyproject_toml}) not found. "
                "Please check the path and try again."
            )

        # get the "packages" from the toml file
        packages_path: str | None = None
        with open(pyproject_toml, "r", encoding="utf-8") as file:
            pyproject_data = toml.load(file)
            packages_path = pyproject_data.get("project", {}).get("source")
            if not packages_path:
                # tool.hatch.build.targets.wheel
                pkg_list = (
                    pyproject_data.get("tool", {})
                    .get("hatch", {})
                    .get("build", {})
                    .get("targets", {})
                    .get("wheel", {})
                    .get("packages", [])
                )
                packages_path = pkg_list[0] if pkg_list else None

        if not packages_path:
            raise RuntimeError(
                "The packages path is not defined in the pyproject.toml file."
            )
        version_file = os.path.join(project_root, packages_path, "version.py")

        self.extract_version_and_write_to_file(pyproject_toml, version_file)
        # do the build
        self.__run_local_clean_up(project_root)
        self.__check_aws_cli_install()
        self.__run_login()
        self.__run_build()

    def publish(self):
        """Publish the artifacts"""
        self.__run_publish()

    def __run_local_clean_up(self, project_root: str):
        """run a local clean up and remove older items in the dist directory"""

        dist_dir = os.path.join(project_root, "dist")
        if os.path.exists(dist_dir):
            # clear it out
            shutil.rmtree(dist_dir)

    def run_remote_clean_up(self):
        """
        Clean out older versions
        """
        logger.warning("warning/info: older versions are not being cleaned out.")

    def extract_version_and_write_to_file(self, pyproject_toml: str, version_file: str):
        """
        extract the version number from the pyproject.toml file and write it
        to the version.py file
        """
        if not os.path.exists(pyproject_toml):
            raise FileNotFoundError(
                f"The pyproject.toml file ({pyproject_toml}) not found. "
                "Please check the path and try again."
            )

        with open(pyproject_toml, "r", encoding="utf-8") as file:
            pyproject_data = toml.load(file)
            version = pyproject_data["project"]["version"]
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(f"__version__ = '{version}'\n")

    def __run_login(self):
        """log into code artifact"""

        commands = f"aws codeartifact login --tool pip --domain {self.domain} --repository {self.repository} ".split()
        self.run_commands(commands=commands)

    def __run_build(self):
        """Run python build commands"""
        self.run_commands(["python", "-m", "build", "--no-isolation"])

    def __run_publish(self):
        """publish to code artifact"""
        self.connect_artifact_to_twine()
        repo_url = self.get_repo_url()

        token = self.get_auth_token()
        # Set up the environment variables for the upload command
        env = os.environ.copy()
        env["TWINE_USERNAME"] = "aws"
        env["TWINE_PASSWORD"] = token
        self.run_commands(
            ["python", "-m", "twine", "upload", "--repository-url", repo_url, "dist/*"],
            env=env,
        )

    def connect_artifact_to_twine(self) -> None:
        """Connect twine to codeartifact"""

        commands = f"aws codeartifact login --tool twine --domain {self.domain} --repository {self.repository} ".split()
        self.run_commands(commands=commands, capture_output=True)

    def get_repo_url(self) -> str:
        """get the artifact repo url"""
        get_url_command = [
            "aws",
            "codeartifact",
            "get-repository-endpoint",
            "--domain",
            self.domain,
            "--domain-owner",
            self.account,
            "--repository",
            self.repository,
            "--format",
            "pypi",
        ]
        repo_url = self.run_commands(get_url_command, capture_output=True)
        if not repo_url:
            print(" ".join(get_url_command))
            raise RuntimeError(
                "No repo url found. "
                "It's most likely that you are not authenticated. "
                "If you are running this locally, you will need to login to AWS and set the correct profile. "
                "for example: aws sso login --profile <your-profile>. "
                "If this is running in a CI/CD pipeline, the you will need to add the correct permissions "
                "to your roles policy."
            )

        repo_url = self.get_url(repo_url)
        if not repo_url:
            raise RuntimeError(
                "No repo url found. "
                "It's most likely that you are not authenticated. "
                "If you are running this locally, you will need to login to AWS and set the correct profile. "
                "for example: aws sso login --profile <your-profile>. "
                "If this is running in a CI/CD pipeline, the you will need to add the correct permissions "
                "to your roles policy."
            )

        return repo_url

    def get_auth_token(self) -> str:
        """get the auth token"""
        commands = [
            "aws",
            "codeartifact",
            "get-authorization-token",
            "--domain",
            self.domain,
            "--domain-owner",
            self.account,
            "--query",
            "authorizationToken",
            "--output",
            "text",
        ]

        token = self.run_commands(commands=commands, capture_output=True)
        if not token:
            raise RuntimeError(
                "No token found. "
                "It's mostlikely that you are not authenticated. "
                "If you are running this locally, you will need to login to AWS and set the correct profile. "
                "for example: aws sso login --profile <your-profile>. "
                "If this is running in a CI/CD pipeline, the you will need to add the correct permissions "
                "to your roles policy."
            )
        return token

    def get_url(self, payload: str):
        """get the url from the payload"""
        if payload is None:
            raise RuntimeError(
                "No payload found for repo url. "
                "It's mostlikely that you are not authenticated. "
                "If you are running this locally, you will need to login to AWS and set the correct profile. "
                "for example: aws sso login --profile <your-profile>. "
                "If this is running in a CI/CD pipeline, the you will need to add the correct permissions "
                "to your roles policy."
            )

        value: dict = json.loads(payload)
        url = value.get("repositoryEndpoint")

        return url

    def run_commands(
        self, commands: List[str], capture_output: bool = False, env=None
    ) -> str | None:
        """centralized area for running process commands"""

        env = env or os.environ.copy()
        config_path = os.path.expanduser("~/.aws/config")
        credentials_path = os.path.expanduser("~/.aws/credentials")
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"The config file ({config_path}) not found. "
                "Please check the path and try again. "
                "If you haven't installed and configured the AWS CLI, you will need to do that first."
            )
        env["AWS_CONFIG_FILE"] = config_path
        env["AWS_SHARED_CREDENTIALS_FILE"] = credentials_path

        if self.profile:
            env["AWS_PROFILE"] = self.profile
        if self.region:
            env["AWS_DEFAULT_REGION"] = self.region

        try:
            whoami = subprocess.run(
                ["whoami"],
                check=True,
                capture_output=capture_output,
            )
            if whoami.stdout:
                output = whoami.stdout.decode().strip()

            # Run the publish command
            result = subprocess.run(
                commands,
                check=True,
                capture_output=capture_output,
                env=env,  # pass any environment vars
            )

            if capture_output:
                output = result.stdout.decode().strip()
                return output

        except subprocess.CalledProcessError as e:
            print("Failed to execute the following command")
            print(" ".join(commands))
            logger.exception(f"An error occurred: {e}")

    import shutil

    def __check_aws_cli_install(self):

        if shutil.which("aws") is None:
            self.__install_aws_cli()

    def __install_aws_cli(self):
        """install the aws cli"""
        # Check if the AWS CLI is installed
        if shutil.which("aws") is not None:
            print("AWS CLI is already installed.")
            return

        # Install the AWS CLI using pip
        try:
            subprocess.run(["pip3", "install", "awscli"], check=True)
            print("AWS CLI installed successfully.")
        except subprocess.CalledProcessError as e:
            print("Failed to install AWS CLI.")
            print(e)
            raise RuntimeError("Failed to install AWS CLI.") from e


def build_and_publish():
    """Build and publish the artifacts"""
    artifacts = AWSCodeArtifactsService()
    artifacts.build()
    artifacts.publish()


def build_only():
    """Build the artifacts without publishing"""
    artifacts = AWSCodeArtifactsService()
    artifacts.build()


def publish_only():
    """Publish the artifacts without building"""
    artifacts = AWSCodeArtifactsService()
    artifacts.publish()


if __name__ == "__main__":
    # For backward compatibility
    build_and_publish()
