from __future__ import annotations

from typing import TYPE_CHECKING
from importlib import import_module

if TYPE_CHECKING:
    from .. import Config


def plugin_interpolate(self: Config, plugin: str, value: str) -> str:
    target_module = import_module(f".{plugin}", "config_manager.plugins")
    output = target_module.interpolate(self, value)
    return output
