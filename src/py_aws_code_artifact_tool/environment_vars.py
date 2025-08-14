import os


class EnvironmentVars:
    """Environment variables"""

    def __init__(self):
        pass

    @property
    def code_artifact_account_number(self):
        """Gets thd code artifacti account number"""
        return os.getenv("CODEARTIFACT_AWS_ACCCOUNT_NUMBER")

    @property
    def code_artifact_domain(self):
        """Gets the code artifact domain"""
        return os.getenv("CODEARTIFACT_DOMAIN")

    @property
    def code_artifact_repository_name(self):
        """Gets the code artifact repository name"""
        return os.getenv("CODEARTIFACT_REPOSITORY_NAME")

    @property
    def code_artifact_repository_region(self):
        """Gets the code artifact repository region"""
        return os.getenv("CODEARTIFACT_REPOSITORY_REGION")

    @property
    def code_artifact_repository_profile(self):
        """Gets the code artifact repository profile"""
        return os.getenv("CODEARTIFACT_REPOSITORY_PROFILE")


environment_vars = EnvironmentVars()
