from pytest import raises
from pathlib import Path
from config_manager import Config
from config_manager.exceptions import NotConfiguredError

CWD = Path(__file__).parent
DATA_DIRECTORY = CWD / "data"


def test_save_config():
    config = Config()
    config.set(path=["group_1", "string"], value="abc", create_path=True)
    config.set(path=["group_1", "int"], value=123, create_path=True)
    config.set(path=["group_1", "float"], value=3.14, create_path=True)
    config.set(path=["group_1", "bool_true"], value=True, create_path=True)
    config.set(path=["group_1", "bool_false"], value=False, create_path=True)
    config.set(path=["nested", "path", "test"], value=0, create_path=True)
    config.set(
        path=["array_group", "sample_array"],
        value=["abc", 123, True],
        create_path=True,
    )

    # INI
    config.config_file = DATA_DIRECTORY / "output.ini"
    config.config_file.unlink(missing_ok=True)
    config.save()
    assert config.config_file.exists()
    config.config_file.unlink()

    # JSON
    config.config_file = DATA_DIRECTORY / "output.json"
    config.config_file.unlink(missing_ok=True)
    config.save()
    assert config.config_file.exists()
    config.config_file.unlink()

    # YAML
    config.config_file = DATA_DIRECTORY / "output.yaml"
    config.config_file.unlink(missing_ok=True)
    config.save()
    assert config.config_file.exists()
    config.config_file.unlink()


def test_load_main():
    config = Config(
        config_file=DATA_DIRECTORY / "test_load_main.json",
    )
    assert config.get_str(["group_1", "config_name"]) == "main"


def test_load_main_with_default():
    config = Config(
        config_file=DATA_DIRECTORY / "test_load_main_with_default-main.ini",
        default_config=DATA_DIRECTORY
        / ("test_load_main_with_default-default.yaml"),
    )
    assert config.get_str(["group_1", "config_name"]) == "main"


def test_create_main_from_default():
    config_file = DATA_DIRECTORY / "test_create_main_from_default-main.yaml"
    config_file.unlink(missing_ok=True)
    with raises(NotConfiguredError):
        Config(
            config_file=config_file,
            default_config=DATA_DIRECTORY
            / ("test_create_main_from_default-default.yaml"),
        )
    config_file.unlink(missing_ok=True)


def test_load_main_with_deploy():
    config = Config(
        config_file=DATA_DIRECTORY / "test_load_main_with_deploy-main.yaml",
        deploy_config=DATA_DIRECTORY
        / ("test_load_main_with_deploy-deploy.ini"),
    )
    assert config.get_str(["group_1", "config_name"]) == "deploy"


def test_load_main_with_default_and_deploy():
    main_config = DATA_DIRECTORY / (
        "test_load_main_with_default_and_deploy-main.json"
    )
    main_config.unlink(missing_ok=True)
    config = Config(
        config_file=DATA_DIRECTORY
        / ("test_load_main_with_default_and_deploy-main.json"),
        default_config=DATA_DIRECTORY
        / ("test_load_main_with_default_and_deploy-default.yaml"),
        deploy_config=DATA_DIRECTORY
        / ("test_load_main_with_default_and_deploy-deploy.ini"),
    )
    assert config.get_str(["group_1", "config_name"]) == "deploy"
    assert config.get_float(["group_1", "default_key"]) == 3.14


def test_load_default_only():
    config = Config(
        default_config=DATA_DIRECTORY / ("test_load_default_only.json")
    )
    assert config.get_str(["group_1", "config_name"]) == "default"


def test_load_deploy_only():
    config = Config(
        default_config=DATA_DIRECTORY / ("test_load_deploy_only.json")
    )
    assert config.get_str(["group_1", "config_name"]) == "deploy"


def test_load_default_and_deploy_only():
    config = Config(
        default_config=DATA_DIRECTORY
        / ("test_load_default_and_deploy_only-default.json"),
        deploy_config=DATA_DIRECTORY
        / ("test_load_default_and_deploy_only-deploy.yaml"),
    )
    assert config.get_str(["group_1", "config_name"]) == "deploy"
    assert config.get_float(["group_1", "default_key"]) == 3.14


def test_interpolate_file():
    config = Config(
        config_file=DATA_DIRECTORY / "test_interpolate_file_config.yaml"
    )
    template_file = DATA_DIRECTORY / "template_file.md"
    output_file = DATA_DIRECTORY / "output_file.md"
    output_file.unlink(missing_ok=True)
    config.interpolate_file(template_file, output_file)
    output_file.unlink(missing_ok=True)
