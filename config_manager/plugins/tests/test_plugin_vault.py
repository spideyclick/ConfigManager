from pathlib import Path
from pytest import raises
from config_manager import Config

CWD = Path(__file__).parent
DATA_DIRECTORY = CWD / "data"


def test_vault():
    config = Config(
        default_config=DATA_DIRECTORY / "test_vault_config-default.yaml",
        config_file=DATA_DIRECTORY / "test_vault_config-main.yaml",
    )
    secret = config.get_str(["secret"])
    secret_value = config.get_str(["secret_value"])
    assert secret == secret_value


def test_vault_not_configured():
    config = Config()
    config.set(["my_secret"], "${vault:/path/to/secret}", create_path=True)
    with raises(KeyError):
        config.get(["my_secret"])
