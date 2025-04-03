import typing
from dataclasses import dataclass


@dataclass
class Dependency:
    folder: str
    github: str
    commit: str
    installed: bool
    current_run_clone: bool
    variables: typing.Dict[str, str]
    additional: typing.Optional[str] = None
