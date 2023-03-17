from pathlib import Path
from config_manager import Config
from pytest import raises

CWD = Path(__file__).parent
DATA_DIRECTORY = CWD / "data"
config = Config(config_file=DATA_DIRECTORY / "config.json")


def test_get_str():
    assert config.get_str(["test_group", "str"]) == "abc"
    assert config.get_str(["test_group", "int"]) == "123"
    assert config.get_str(["test_group", "float"]) == "3.14"
    assert config.get_str(["test_group", "bool_true"]) == "True"
    assert config.get_str(["test_group", "bool_false"]) == "False"
    with raises(KeyError):
        config.get_str(["_", "_"])
    with raises(KeyError):
        config.get_str(["test_group", "_"])


def test_get_int():
    with raises(ValueError):
        config.get_int(["test_group", "str"])
    assert config.get_int(["test_group", "int"]) == 123
    assert config.get_int(["test", "deep", "nesting"]) == 0
    assert config.get_int(["test_group", "float"]) == 3
    with raises(ValueError):
        config.get_int(["test_group", "bool_true"])
    with raises(ValueError):
        config.get_int(["test_group", "bool_false"])
    with raises(KeyError):
        config.get_int(["_", "_"])
    with raises(KeyError):
        config.get_int(["test_group", "_"])


def test_get_float():
    with raises(ValueError):
        config.get_float(["test_group", "str"])
    assert config.get_float(["test_group", "int"]) == 123.0
    assert config.get_float(["test_group", "float"]) == 3.14
    with raises(ValueError):
        config.get_float(["test_group", "bool_true"])
    with raises(ValueError):
        config.get_float(["test_group", "bool_false"])
    with raises(KeyError):
        config.get_float(["_", "_"])
    with raises(KeyError):
        config.get_float(["test_group", "_"])


def test_get_bool():
    assert config.get_bool(["test_group", "str"]) is False
    with raises(ValueError):
        config.get_bool(["test_group", "int"])
    with raises(ValueError):
        config.get_bool(["test_group", "float"])
    assert config.get_bool(["test_group", "bool_true"]) is True
    assert config.get_bool(["test_group", "bool_false"]) is False
    with raises(KeyError):
        config.get_bool(["_", "_"])
    with raises(KeyError):
        config.get_bool(["test_group", "_"])


def test_get_dict():
    with raises(ValueError):
        config.get_dict(["test_group", "str"])
    with raises(ValueError):
        config.get_dict(["test_group", "str"])
    assert config.get_dict(["test_group"]) == {
        "str": "abc",
        "int": 123,
        "float": 3.14,
        "bool_true": True,
        "bool_false": False,
    }
    with raises(KeyError):
        config.get_bool(["_", "_"])
    with raises(KeyError):
        config.get_bool(["test_group", "_"])


def test_get_list():
    with raises(ValueError):
        config.get_dict(["test_group", "str"])
    assert config.get_list(["array_group"]) == ["abc", 123, True]
    with raises(KeyError):
        config.get_list(["_", "_"])
    with raises(KeyError):
        config.get_list(["test_group", "_"])
