from json import dumps as dump_json, loads as load_json
from pathlib import Path


def load(path: Path) -> dict:
    file_content = path.read_text()
    output = load_json(file_content)
    return output


def save(path: Path, data: dict):
    output = dump_json(data, indent=2)
    path.write_text(output)
