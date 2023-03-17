from importlib import import_module
from pathlib import Path


def load(path: Path) -> dict:
    try:
        target_module = import_module(path.suffix, "config_manager.storage")
        output = target_module.load(path)
        return output
    except ModuleNotFoundError as e:
        m = (
            f"Loading configuration data from file of type {path.suffix} is "
            "not yet supported."
        )
        raise NotImplementedError(m) from e


def save(path: Path, data: dict) -> None:
    """
    Write configurations to a configuration file.
    """
    try:
        target_module = import_module(path.suffix, "config_manager.storage")
        target_module.save(path, data)
    except ModuleNotFoundError as e:
        m = (
            f"Loading configuration data from file of type {path.suffix} is "
            "not yet supported."
        )
        raise NotImplementedError(m) from e
