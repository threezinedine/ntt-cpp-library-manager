import os
import json
import logging
import argparse
import contants
import git_utils
import cmake_utils
from dependency import Dependency
from colorama import Fore, Style, init

init()

parser = argparse.ArgumentParser(
    description="NTT Lib Manager for auto organizing the dependencies of the project."
)

parser.add_argument(
    "--output-folder",
    "-of",
    type=str,
    default=contants.VENDOR_FOLDER,
    help="The folder name of the output dependencies.",
)

parser.add_argument(
    "--update",
    "-u",
    action="store_true",
    help="Used for updating dependencies if the commit has been changed or be modified.",
)

args = parser.parse_args()


class ColorFormatter(logging.Formatter):
    def format(self, record):
        format_orig = self._style._fmt
        if record.levelno == logging.ERROR:
            self._style._fmt = f"{Fore.RED}{format_orig}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            self._style._fmt = f"{Fore.YELLOW}{format_orig}{Style.RESET_ALL}"
        elif record.levelno == logging.INFO:
            self._style._fmt = f"{Fore.GREEN}{format_orig}{Style.RESET_ALL}"
        elif record.levelno == logging.DEBUG:
            self._style._fmt = f"{Fore.BLUE}{format_orig}{Style.RESET_ALL}"

        result = logging.Formatter.format(self, record)
        self._style._fmt = format_orig

        return result


logger = logging.getLogger(contants.LOGGER_NAME)
logger.setLevel(contants.LOG_LEVEL)


logger.handlers.clear()
formatter = ColorFormatter(
    "[%(levelname)s] - %(asctime)s - %(filename)s:%(lineno)d - %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def validate_config_file(config: dict) -> bool:
    if "version" not in config:
        logger.error("The version field is required in the config file.")
        return False

    if "dependencies" not in config:
        logger.error("The dependencies field is required in the config file.")
        return False

    if not isinstance(config["dependencies"], list):
        logger.error("The dependencies field must be a list.")
        return False

    for dependency in config["dependencies"]:
        if "github" not in dependency:
            logger.error("The github field is required in the dependencies list.")
            return False

        if "folder" not in dependency:
            logger.error("The folder field is required in the dependencies list.")
            return False

    return True


if __name__ == "__main__":
    logger.info("Start building the project...")

    logger.info(f"Start reading the {contants.CONFIG_FILE_NAME} file...")

    if not os.path.exists(contants.CONFIG_FILE_NAME):
        logger.error(f"The {contants.CONFIG_FILE_NAME} file does not exist.")
        exit(1)

    with open(contants.CONFIG_FILE_NAME, "r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse the {contants.CONFIG_FILE_NAME} file: {e}")
            exit(1)

    logger.info(f"The config file is read successfully.")

    if not validate_config_file(config):
        exit(1)

    logger.info(f"The version of the project is {config['version']}.")

    logger.info("Start processing the dependencies...")

    dependencies = {}

    if not os.path.exists(args.output_folder):
        logger.info(f"The output folder {args.output_folder} does not exist.")
        os.makedirs(args.output_folder)

    for dependency in config["dependencies"]:
        if dependency["folder"] in dependencies:
            continue

        dependencies[dependency["folder"]] = Dependency(
            folder=dependency["folder"],
            github=dependency["github"],
            commit=dependency["commit"] if "commit" in dependency else None,
            installed=False,
            current_run_clone=False,
            variables=dependency["variables"] if "variables" in dependency else {},
            additional=dependency["additional"] if "additional" in dependency else None,
        )

    for dependency in dependencies.values():
        if dependency.installed:
            continue

        logger.info(f"Processing the dependency: {dependency.folder}...")

        vendor_folder = os.path.join(args.output_folder, dependency.folder)

        if not git_utils.is_git_repo(vendor_folder):
            if os.path.exists(vendor_folder):
                os.remove(vendor_folder)
        else:
            logger.info(f"The dependency {dependency.folder} is already installed.")
            dependency.installed = True
            continue

        if not git_utils.clone_repository(dependency.github, vendor_folder):
            exit(1)

        dependency.current_run_clone = True

        if dependency.commit:
            git_utils.modify_repository_commit(vendor_folder, dependency.commit)

        dependency.installed = True

    if args.update:
        logger.debug("Start updating all dependencies...")
        for dependency in dependencies.values():
            if dependency.current_run_clone:
                logger.info(f"The dependency {dependency.folder} is updated.")
                continue

            vendor_folder = os.path.join(args.output_folder, dependency.folder)
            if dependency.commit is None or not git_utils.check_commit_match(
                vendor_folder,
                dependency.commit,
            ):
                logger.info(f"Updating the dependency: {dependency.folder}...")
                git_utils.modify_repository_commit(vendor_folder, dependency.commit)

    cmake_utils.generate_vendor_cmake(dependencies.values(), args.output_folder)

    logger.info("All dependencies are processed successfully.")
