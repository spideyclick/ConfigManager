from config_manager import Config
from pytest import raises


def test_var_lookup():
    config = Config()
    config.set(
        path=["path", "to", "value"],
        value=3.14,
        create_path=True,
    )
    config.set(
        path=["lookup_value"],
        value="${var:/path/to/value}",
        create_path=True,
    )
    assert config.get_float(["lookup_value"]) == 3.14


def test_bad_var_lookup():
    config = Config()
    config.set(
        path=["bad_lookup_value"],
        value="${var:/path/to/nonexistent/value}",
        create_path=True,
    )
    with raises(KeyError):
        config.get(["bad_lookup_value"])
