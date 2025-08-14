import subprocess
import sys
import os
from aws_lambda_powertools import Logger
from devops.code_artifacts.environment_vars import environment_vars

logger = Logger()


def is_logged_in():
    """Check to see if i'm logged in"""
    try:
        commands = ["aws", "codeartifact", "list-repositories"]
        profile = environment_vars.code_artifact_repository_profile
        if profile:
            commands.append("--profile")
            commands.append(profile)
        result = subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.returncode == 0
    except Exception as e:  # pylint: disable=w0718
        logger.exception(f"Error checking login status: {e}")
        return False


def run_setup():
    """Run the setup"""
    try:
        subprocess.check_call([sys.executable, "./devops/pip_code_artifact_setup.py"])
    except subprocess.CalledProcessError as e:
        logger.exception(f"Setup script failed: {e}")
        sys.exit(1)


if not is_logged_in():
    logger.info("Not logged in to CodeArtifact. Running setup script...")
    run_setup()
else:
    logger.info("Already logged in to CodeArtifact.")
