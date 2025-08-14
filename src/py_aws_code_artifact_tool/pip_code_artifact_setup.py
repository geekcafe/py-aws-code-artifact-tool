import os
import subprocess
from aws_lambda_powertools import Logger
from devops.code_artifacts.environment_vars import environment_vars

logger = Logger()


def setup_codeartifact_pip(
    account_number: str,
    domain: str,
    repository: str,
    region: str,
    profile: str | None = None,
):
    # Get the AWS account ID
    # sts_client = boto3.client('sts')
    # account_id = sts_client.get_caller_identity().get('Account')

    # Authenticate pip with CodeArtifact
    login_command = [
        "aws",
        "codeartifact",
        "login",
        "--tool",
        "pip",
        "--domain",
        domain,
        "--domain-owner",
        account_number,
        "--repository",
        repository,
        "--region",
        region,
    ]
    if profile:
        login_command.extend(["--profile", profile])

    result: subprocess.CompletedProcess = None
    try:
        result = subprocess.run(
            login_command, capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error("Failed to authenticate pip with CodeArtifact.")
        # logger.error("Command output:", result.stdout)
        # logger.error("Error output:", result.stderr)
        logger.error("Exception:", e)
        profile_info = f" Using profile {profile}" if profile else ""

        if "sso" in str(e.stderr).lower():
            logger.error(
                "Failed to authenticate pip with CodeArtifact. "
                "Please check your SSO configuration. "
                f"{profile_info}"
            )
            raise RuntimeError(
                "Failed to authenticate pip with CodeArtifact. "
                "Please check your SSO configuration. "
                f"{profile_info}"
            ) from e
        # raise RuntimeError("CodeArtifact login failed") from e
        else:
            raise RuntimeError(f"CodeArtifact login failed: {e.stderr}") from e
    except Exception as e:  # pylint: disable=w0718
        logger.error("Failed to authenticate pip with CodeArtifact.")
        # logger.error("Command output:", result.stdout)
        # logger.error("Error output:", result.stderr)
        logger.error("Exception:", e)
        profile_info = f" Using profile {profile}" if profile else ""

        message = f"Failed to authenticate pip with CodeArtifact {profile_info} "
        raise RuntimeError(message) from e

    if result.returncode != 0:
        logger.error("Failed to authenticate pip with CodeArtifact.")
        logger.error("Command output:", result.stdout)
        logger.error("Error output:", result.stderr)
        raise RuntimeError("CodeArtifact login failed")

    logger.info("Successfully authenticated pip with CodeArtifact.")
    logger.info("Command output:", result.stdout)

    logger.info(
        f"Configured pip to use CodeArtifact repository {repository} in domain {domain}."
    )


def main():
    setup_codeartifact_pip(
        account_number=environment_vars.code_artifact_account_number,
        domain=environment_vars.code_artifact_domain,
        repository=environment_vars.code_artifact_repository_name,
        region=environment_vars.code_artifact_repository_region,
        profile=environment_vars.code_artifact_repository_profile,
    )


if __name__ == "__main__":
    main()
