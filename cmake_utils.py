import os
import typing
import logging
import contants
from dependency import Dependency


logger = logging.getLogger(contants.LOGGER_NAME)


def generate_vendor_cmake(
    dependencies: typing.List[Dependency],
    output_folder: str = contants.VENDOR_FOLDER,
):
    if not os.path.exists(output_folder):
        logger.error(f"The {output_folder} folder does not exist.")
        exit(1)

    if not os.path.exists(os.path.join(output_folder, "CMakeLists.txt")):
        logger.info(
            f"Creating the {os.path.join(output_folder, 'CMakeLists.txt')} file..."
        )
        with open(os.path.join(output_folder, "CMakeLists.txt"), "w") as f:
            f.write("")

    content = ""

    sorted_dependencies = sorted(dependencies, key=lambda x: x.index, reverse=True)

    for dependency in sorted_dependencies:
        content += dependency.to_cmake_string()

    with open(os.path.join(output_folder, "CMakeLists.txt"), "w") as f:
        f.write(content)

    logger.info(
        f"The {os.path.join(output_folder, 'CMakeLists.txt')} file has been generated."
    )
