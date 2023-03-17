from __future__ import annotations

from re import search, finditer, sub
from typing import Any, TYPE_CHECKING
from pathlib import Path
from json import dumps as dump_json

if TYPE_CHECKING:
    from . import Config

from .tools import get_nested_value, set_nested_value, merge_dictionaries
from .storage import save as save_to_file, load as load_file
from .plugins import plugin_interpolate
from .exceptions import NotConfiguredError
from .settings import DEFAULT_INTERPOLATION_PATTERN


def parse_path(self: Config, path: str | list[str]) -> list[str]:
    if isinstance(path, list):
        return path
    output = path.strip(self.path_delimiter).split(self.path_delimiter)
    return output


def save(self: Config) -> None:
    """
    Write configurations to a configuration file.
    """
    if self.config_file is None:
        m = "Attribute config_file must be set to save to disk"
        raise AttributeError(m)
    save_to_file(path=self.config_file, data=self.entries)


def load(self: Config):
    config_untouched = False
    if self.default_config:
        merge_dictionaries(load_file(self.default_config), self.entries)
    if (
        self.default_config
        and self.config_file
        and not self.config_file.exists()
    ):
        self.save()
        config_untouched = True
    elif self.config_file:
        merge_dictionaries(load_file(self.config_file), self.entries)
    if self.deploy_config:
        merge_dictionaries(load_file(self.deploy_config), self.entries)
        config_untouched = False
    if self.deploy_config and self.config_file:
        self.save()
    if config_untouched:
        m = (
            "This application has not yet been configured. "
            f"Please edit configuration file at {self.config_file} or provide "
            "a deployment configuration file to run this application."
        )
        raise NotConfiguredError(m)


def set(
    self: Config,
    path: str | list,
    value: Any,
    create_path: bool = False,
) -> None:
    """
    Sets a value by path, parsing arrays and objects as needed. Optionally can
    create path in entries if it does not exist.
    """
    set_nested_value(
        path=self.parse_path(path),
        value=value,
        input=self.entries,
        create_path=create_path,
    )


def get(self: Config, path: list | str):
    """
    Gets a value by path, interpolating variables and secrets. When using this
    function, there are no guarantees about the type.
    """
    value = get_nested_value(path=self.parse_path(path), input=self.entries)
    if isinstance(value, str) and search(self.interpolation_pattern, value):
        value = self.interpolate(value)
    return value


def get_str(self: Config, path: list | str) -> str:
    value = self.get(self.parse_path(path))
    if isinstance(value, (dict, list)):
        return dump_json(value, indent=2)
    return str(value)


def get_int(self: Config, path: list | str) -> int:
    value = self.get(self.parse_path(path))
    if isinstance(value, str) and "." in value:
        value = float(value)
    if isinstance(value, bool):
        m = (
            "get_int wants to return an int, but the value is a bool."
            "get_int does not assume translation between those types."
            "If you want to convert this value to an integer, please call "
            "get_bool and convert from there."
        )
        raise ValueError(m)
    return int(value)


def get_float(self: Config, path: list | str) -> float:
    value = self.get(self.parse_path(path))
    if isinstance(value, bool):
        m = (
            "get_float wants to return a float, but the value is a bool."
            "get_float does not assume translation between those types."
            "If you want to convert this value to a float, please call "
            "get_bool and convert from there."
        )
        raise ValueError(m)
    return float(value)


def get_bool(self: Config, path: list | str) -> bool:
    value = self.get(self.parse_path(path))
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    m = (
        "get_bool wants to return a boolean value, but the value is of type "
        f"{type(value)}. get_bool does not assume translation from that type."
    )
    raise ValueError(m)


def get_dict(self: Config, path: list | str) -> dict:
    value = self.get(self.parse_path(path))
    if not isinstance(value, dict):
        m = (
            "get_dict requires a return value of type dict; "
            f"fetched value {value} is of type {type(value)}"
        )
        raise ValueError(m)
    return value


def get_list(self: Config, path: list | str) -> list:
    value = self.get(self.parse_path(path))
    if not isinstance(value, list):
        m = (
            "get_list requires a return value of type list; "
            f"fetched value {value} is of type {type(value)}"
        )
        raise ValueError(m)
    return value


def interpolate(
    self: Config,
    value: str,
    interpolation_pattern: str = DEFAULT_INTERPOLATION_PATTERN,
) -> str:
    """
    Takes a value and interpolates the references to other fields and
    functions, returning a fully rendered value.
    """
    new_value = value
    for entry in finditer(interpolation_pattern, value):
        start = entry.start()
        end = entry.end()
        interpolation_text = value[start:end]
        plugin = sub(interpolation_pattern, "\\1", interpolation_text)
        initial_value = sub(interpolation_pattern, "\\2", interpolation_text)
        result = plugin_interpolate(self, plugin, initial_value)
        new_value = new_value.replace(interpolation_text, result)
    return new_value


def interpolate_file(
    self: Config,
    template_file: Path,
    destination_file: Path | None = None,
) -> None:
    """
    Takes a given template file and searches for all matches to the
    interpolation pattern. Interpolates all patterns found with loaded config.

    Changes are either written to template_file or destination_file if provided.
    """
    new_contents = ""
    if destination_file is None:
        destination_file = template_file
    for line in template_file.read_text().splitlines():
        new_contents += self.interpolate(line) + "\n"
    destination_file.write_text(new_contents)
