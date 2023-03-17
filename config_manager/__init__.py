from pathlib import Path
from .settings import DEFAULT_INTERPOLATION_PATTERN, DEFAULT_PATH_DELIMITER


def parse_file_parameter(input: Path | str | None) -> Path | None:
    if input is None or isinstance(input, Path):
        return input
    if not isinstance(input, str):
        raise ValueError("File must be None, a Path, or a string")
    input = input.strip()
    if input == "":
        raise ValueError("File must not be an empty string")
    return Path(input)


class Config:
    """
    Config is an object to represent the data contained in one or more files.
    The goal is to safely read and write configuration data while allowing for
    secure secret access and robust interpolation.
    """

    def __init__(
        self,
        config_file: Path | str | None = None,
        default_config: Path | str | None = None,
        deploy_config: Path | str | None = None,
        interpolation_pattern: str = DEFAULT_INTERPOLATION_PATTERN,
        path_delimiter: str = DEFAULT_PATH_DELIMITER,
        entries: dict = {},
    ):
        self.config_file: Path | None = parse_file_parameter(config_file)
        self.default_config: Path | None = parse_file_parameter(default_config)
        self.deploy_config: Path | None = parse_file_parameter(deploy_config)
        self.interpolation_pattern: str = interpolation_pattern
        self.path_delimiter: str = path_delimiter
        self.entries: dict = entries
        self.load()

    from .methods import (
        get,
        get_str,
        get_int,
        get_float,
        get_bool,
        get_dict,
        get_list,
        set,
        save,
        load,
        interpolate,
        interpolate_file,
        parse_path,
    )
