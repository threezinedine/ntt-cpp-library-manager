import os
import typing
import subprocess
import logging
from urllib.parse import urlparse

logger = logging.getLogger("NTT Lib Manager")


def is_git_repo(folder_path):
    """
    Check if the given folder is a valid Git repository.

    Args:
        folder_path (str): Path to the folder to check

    Returns:
        bool: True if it's a valid Git repository, False otherwise
    """
    try:
        # Check if the folder exists
        if not os.path.exists(folder_path):
            logger.debug(f"The folder {folder_path} does not exist.")
            return False

        git_dir = os.path.join(folder_path, ".git")
        if not os.path.exists(git_dir):
            logger.debug(f"The folder {folder_path} is not a valid Git repository.")
            return False

        essential_files = ["HEAD", "config", "refs"]
        for file in essential_files:
            file_path = os.path.join(git_dir, file)
            if not os.path.exists(file_path):
                logger.debug(f"The file {file_path} does not exist.")
                return False

        return True

    except subprocess.CalledProcessError as e:
        logger.error(
            f"An error occurred while checking if the folder {folder_path} is a valid Git repository."
        )
        return False
    except Exception as e:
        logger.error(
            f"An error occurred while checking if the folder {folder_path} is a valid Git repository."
        )
        return False


def check_commit_match(folder_path, target_commit) -> bool:
    """
    Check if the current commit in the repository matches the target commit.

    Args:
        folder_path (str): Path to the Git repository
        target_commit (str): The commit hash to check against (can be full or short hash)

    Returns:
        bool: True if commits match, False otherwise
    """
    try:
        if not is_git_repo(folder_path):
            logger.debug(f"The folder {folder_path} is not a valid Git repository.")
            return False

        # Get current commit hash
        current_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=folder_path,
            capture_output=True,
            text=True,
        )

        if current_commit.returncode != 0:
            logger.debug(
                f"Failed to get the current commit hash for the folder {folder_path}."
            )
            return False

        target_full_hash = subprocess.run(
            ["git", "rev-parse", target_commit],
            cwd=folder_path,
            capture_output=True,
            text=True,
        )

        if target_full_hash.returncode != 0:
            logger.debug(
                f"Failed to get the target commit hash for the folder {folder_path}."
            )
            return False

        current_hash = current_commit.stdout.strip()
        target_hash = target_full_hash.stdout.strip()

        logger.debug(f"Current hash: {current_hash}")
        logger.debug(f"Target hash: {target_hash}")

        if current_hash == target_hash:
            commit_details = subprocess.run(
                ["git", "show", "-s", "--format=%an <%ae>%n%B", current_hash],
                cwd=folder_path,
                capture_output=True,
                text=True,
            )

            if commit_details.returncode == 0:
                logger.debug(f"Commit Details: {commit_details.stdout}")

            return True
        else:
            logger.debug(
                f"The commit hash of the folder {folder_path} does not match the target commit."
            )
            return False

    except subprocess.CalledProcessError as e:
        logger.error(
            f"An error occurred while checking the commit hash of the folder {folder_path}."
        )
        return False
    except Exception as e:
        logger.error(
            f"An error occurred while checking the commit hash of the folder {folder_path}. Error: {e}"
        )
        return False


def validate_github_url(url: str) -> bool:
    parsed_url = urlparse(url)
    return parsed_url.scheme == "https" and parsed_url.netloc == "github.com"


def clone_repository(url: str, folder: str) -> bool:
    if not validate_github_url(url):
        logger.error(f"The URL {url} is not a valid GitHub URL.")
        return False

    try:
        logger.info(f"Cloning the repository {url}...")
        subprocess.run(["git", "clone", url, folder])

        logger.info(f"Clone the repository successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone the repository: {e}")
        return False

    return True


def modify_repository_commit(folder: str, commit: typing.Optional[str] = None) -> bool:
    try:
        subprocess.run(
            ["git", "fetch"],
            cwd=folder,
            capture_output=False,
            stdout=subprocess.DEVNULL,
        )

        if commit is not None:
            subprocess.run(
                ["git", "checkout", commit],
                cwd=folder,
                capture_output=False,
                stdout=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=folder,
                capture_output=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to checkout the commit: {e}")
        return False

    return True
