import os
import json
import utils
import typing
import logging
import contants
import git_utils
from dataclasses import dataclass, field

logger = logging.getLogger(contants.LOGGER_NAME)


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


@dataclass
class Condition:
    variables: typing.Dict[str, str] = field(default_factory=dict)
    additionals: typing.List[str] = field(default_factory=list)

    def to_cmake_string(self, prefix: str = "") -> str:
        cmake_string = ""

        for variable_name, variable_value in self.variables.items():
            cmake_string += f"{prefix}set({variable_name} {variable_value})\n"

        for additional in self.additionals:
            cmake_string += f"{prefix}{additional}\n"

        return cmake_string


@dataclass
class Dependency:
    folder: str = field(default="")
    github: str = field(default="")
    commit: str = field(default="")
    global_condition: Condition = field(default_factory=Condition)
    other_conditions: typing.Dict[str, Condition] = field(default_factory=dict)

    index: int = field(default=0)
    child_dependencies: typing.List["Dependency"] = field(default_factory=list)

    def is_installed(self, vendor_folder: str) -> bool:
        return git_utils.is_git_repo(
            os.path.join(
                vendor_folder,
                self.folder,
            ),
        )

    def install(self, vendor_folder: str) -> None:
        git_utils.clone_repository(
            self.github,
            os.path.join(vendor_folder, self.folder),
        )

    def has_child_dependencies(self, vendor_folder: str) -> bool:
        config_file = os.path.join(
            vendor_folder,
            self.folder,
            contants.CONFIG_FILE_NAME,
        )

        if not os.path.exists(config_file):
            return False

        with open(config_file, "r") as f:
            config = json.load(f)

        return validate_config_file(config)

    def increase_index(self) -> None:
        self.index += 1

        for child_dependency in self.child_dependencies:
            child_dependency.increase_index()

    def to_cmake_string(self) -> str:
        cmake_string = ""

        cmake_string += (
            f"######## Variables for the {self.folder} dependency ########\n"
        )
        cmake_string += self.global_condition.to_cmake_string()

        cmake_string += (
            "######## End of the variables for the {self.folder} dependency ########\n"
        )
        cmake_string += (
            f"######## Conditions for the {self.folder} dependency ########\n"
        )

        for condition_name, condition in self.other_conditions.items():
            cmake_string += f"if({condition_name})\n"
            condition_ins = condition
            if not isinstance(condition, Condition):
                condition_ins = utils.dict_to_dataclass(condition, Condition)

            cmake_string += condition_ins.to_cmake_string("\t")

            cmake_string += f"endif()\n"

        cmake_string += (
            "######## End of the conditions for the {self.folder} dependency ########\n"
        )

        cmake_string += f"add_subdirectory({self.folder})\n"

        return cmake_string

    def __repr__(self) -> str:
        return f"<Dependency folder={self.folder} index={self.index} numberChildren={len(self.child_dependencies)}>"
