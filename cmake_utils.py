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

    for dependency in dependencies:
        content += f"####### Start adding the {dependency.folder} #######\n"

        has_variables = False
        for variable_name, variable_value in dependency.variables.items():
            content += f"set({variable_name} {variable_value})\n"
            has_variables = True

        if dependency.additional:
            content += f"{dependency.additional}\n"
            has_variables = True

        if has_variables:
            content += "\n"

        content += f"add_subdirectory({dependency.folder})\n"

        content += f"####### End adding the {dependency.folder} #######\n\n"

    with open(os.path.join(output_folder, "CMakeLists.txt"), "w") as f:
        f.write(content)

    logger.info(
        f"The {os.path.join(output_folder, 'CMakeLists.txt')} file has been generated."
    )
