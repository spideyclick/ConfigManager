from yaml import safe_load as load_yaml, dump
from pathlib import Path


def load(path: Path) -> dict:
    file_content = path.read_text()
    output = load_yaml(file_content)
    if output is None:
        output = {}
    return output


def save(path: Path, data: dict):
    output = dump(data)
    path.write_text(output)
