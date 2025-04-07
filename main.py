import os
import json
import utils
import logging
import argparse
import contants
import git_utils
import dependency
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


def get_dependencies_from_path(
    vendor_folder: str,
    current_dependency: Dependency,
    dependencies: list[Dependency],
) -> bool:
    config_file = os.path.join(
        vendor_folder,
        current_dependency.folder,
        contants.CONFIG_FILE_NAME,
    )
    ## Add all dependencies of the current dependency
    if not os.path.exists(config_file):
        return False

    with open(config_file, "r") as f:
        vendor_config = json.load(f)

    new_dependencies = []

    for dependency in vendor_config["dependencies"]:
        child_dependency = None

        if dependency["folder"] in [dependency.folder for dependency in dependencies]:
            for dep in dependencies:
                if dep.folder == dependency["folder"]:
                    child_dependency = dep
                    break

            if child_dependency is None:
                logger.error(
                    f"The dependency {dependency['folder']} does not exist in the dependencies list."
                )
                exit(1)
        else:
            child_dependency = utils.dict_to_dataclass(dependency, Dependency)
            new_dependencies.append(child_dependency)

        current_dependency.child_dependencies.append(child_dependency)

    dependencies.extend(new_dependencies)

    should_install_dependencies = False
    for dependency in new_dependencies:
        if not dependency.is_installed(vendor_folder):
            should_install_dependencies = True
            break

    return should_install_dependencies


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

    if not dependency.validate_config_file(config):
        exit(1)

    if not os.path.exists(args.output_folder):
        logger.info(f"The output folder {args.output_folder} does not exist.")
        os.makedirs(args.output_folder)

    logger.info(f"The version of the project is {config['version']}.")

    logger.info("Start processing the dependencies...")

    dependencies = [
        utils.dict_to_dataclass(dependency, Dependency)
        for dependency in config["dependencies"]
    ]

    logger.debug(f"Dependencies: {dependencies}")

    while True:
        has_dependency_to_install = False
        dependenciesClone = dependencies.copy()

        for dependency in dependenciesClone:
            logger.info(f"Processing the dependency: {dependency.folder}...")
            if not dependency.is_installed(args.output_folder):
                logger.info(f"The dependency {dependency.folder} is not installed.")
                logger.info(f"Processing the dependency: {dependency.folder}...")
                dependency.install(args.output_folder)
            else:
                logger.info(f"The dependency {dependency.folder} is already installed.")

            if dependency.has_child_dependencies(args.output_folder):
                logger.info(
                    f"The dependency {dependency.folder} has child dependencies."
                )
                has_dependency_to_install = (
                    has_dependency_to_install
                    or get_dependencies_from_path(
                        args.output_folder,
                        dependency,
                        dependencies,
                    )
                )

                logger.debug(f"New dependencies: {dependencies}")
            else:
                logger.info(
                    f"The dependency {dependency.folder} has no child dependencies."
                )

        if not has_dependency_to_install:
            break

    logger.info("Increasing the index of the dependencies...")
    for dependency in dependencies:
        dependency.increase_index()

    logger.debug(f"Increased index of the dependencies: {dependencies}")

    cmake_utils.generate_vendor_cmake(dependencies, args.output_folder)

    if args.update:
        for dependency in dependencies:
            git_utils.modify_repository_commit(
                os.path.join(args.output_folder, dependency.folder)
            )

    logger.info("All dependencies are processed successfully.")
