from pathlib import Path
from re import match, sub
from json import dumps as dump_json


COMMENT_PREFIXES: list[str] = [
    ";",
    "#",
    "/",
]
GROUP_PATTERN = r"^\[(.+)\]$"
ENTRY_PATTERN = r"^([\S]*)[ ]*=[ ]*(.*)$"


def load(path: Path) -> dict:
    output = {}
    current_group = None
    file_content = path.read_text()
    for line in file_content.splitlines():
        line = line.strip()
        if not line:
            continue
        elif line[0] in COMMENT_PREFIXES:
            continue
        elif match(GROUP_PATTERN, line):
            current_group = sub(GROUP_PATTERN, "\\1", line)
            if current_group not in output.keys():
                output[current_group] = {}
        elif match(ENTRY_PATTERN, line):
            key = sub(ENTRY_PATTERN, "\\1", line)
            value = sub(ENTRY_PATTERN, "\\2", line)
            output[current_group][key] = value
    return output


def save(path: Path, data: dict):
    new_file = ""
    for group, keys in data.items():
        new_file += f"[{group}]\n"
        for key, value in keys.items():
            if isinstance(value, (list, dict, bool)):
                new_file += f"{key} = {dump_json(value)}\n"
                continue
            new_file += f"{key} = {value}\n"
        new_file += "\n"
    path.write_text(new_file)
