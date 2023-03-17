from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import Config
from ..settings import DEFAULT_PATH_DELIMITER


def interpolate(
    self: Config,
    value: str,
    path_delimiter: str = DEFAULT_PATH_DELIMITER,
) -> str:
    path = value.strip(path_delimiter).split(path_delimiter)
    output = self.get_str(path=path)
    return output
