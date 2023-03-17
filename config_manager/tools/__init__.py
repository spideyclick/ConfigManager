from typing import Any


def merge_dictionaries(source: dict, destination: dict) -> None:
    """
    Recursively merge dictionaries.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge_dictionaries(value, node)
        else:
            destination[key] = value


def get_nested_value(path: list[str], input: dict | list) -> Any:
    """
    Get a value from a nested dictionary.
    """
    if len(path) == 1:
        if isinstance(input, list):
            return input[int(path[0])]
        return input[path[0]]
    if isinstance(input, list):
        return get_nested_value(path[1:], input[int(path[0])])
    return get_nested_value(path[1:], input[path[0]])


def set_nested_value(
    path: list[str],
    value: Any,
    input: dict | list,
    create_path: bool = False,
) -> None:
    """
    Get a value from a nested dictionary.
    """
    if len(path) == 1:
        if isinstance(input, list):
            input[int(path[0])] = value
            return
        if isinstance(input, dict):
            input[path[0]] = value
            return
        m = f"Cannot assign value {value} to input of type {type(input)}"
        raise ValueError(m)
    if isinstance(input, list):
        set_nested_value(path[1:], value, input[int(path[0])], create_path)
        return
    elif isinstance(input, dict):
        if create_path and path[0] not in input:
            input[path[0]] = {}
        set_nested_value(path[1:], value, input[path[0]], create_path)
        return
    m = (
        f"Cannot traverse path {path}: encountered value {value} instead of "
        "dict or list"
    )
    raise ValueError(m)
