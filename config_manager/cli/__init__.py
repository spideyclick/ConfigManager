import click
from pathlib import Path
from json import dumps as dump_json
from config_manager import Config
import functools


def get_config_options(f):
    @click.option(
        "-c",
        "--config-file",
        type=click.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            writable=True,
            path_type=Path,
        ),
        required=True,
    )
    @click.option(
        "--default-config",
        type=click.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            writable=False,
            path_type=Path,
        ),
        required=False,
    )
    @click.option(
        "--deploy-config",
        type=click.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            writable=False,
            path_type=Path,
        ),
        required=False,
    )
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


@click.group()
def cli():
    pass


@cli.command()
@get_config_options
@click.argument("path", type=str)
def get(
    config_file: Path,
    default_config: Path,
    deploy_config: Path,
    path: str,
):
    """
    Get a single value from a config file.
    """
    config = Config(
        config_file=config_file,
        default_config=default_config,
        deploy_config=deploy_config,
    )
    output = config.get_str(path)
    print(output, end=None)


@cli.command()
@get_config_options
@click.argument("path", type=str)
@click.argument("value", type=str)
def set(
    config_file: Path,
    default_config: Path,
    deploy_config: Path,
    path: str,
    value: str,
):
    """
    Add or update a configuration value. If the value does not yet exist, it
    will be created.
    """
    config = Config(
        config_file=config_file,
        default_config=default_config,
        deploy_config=deploy_config,
    )
    config.set(path=path, value=value, create_path=True)
    config.save()


@cli.command()
@get_config_options
def export(config_file: Path, default_config: Path, deploy_config: Path):
    """
    Export configuration as JSON to stdout.
    """
    config = Config(
        config_file=config_file,
        default_config=default_config,
        deploy_config=deploy_config,
    )
    print(dump_json(config.entries, indent=2))


@cli.command()
@get_config_options
@click.option(
    "--template",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=True,
        path_type=Path,
    ),
    required=True,
)
@click.option(
    "--output",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        writable=True,
        path_type=Path,
    ),
    required=False,
)
def build(
    config_file: Path,
    default_config: Path,
    deploy_config: Path,
    template: Path,
    output: Path | None = None,
):
    """
    Fill a template file with values from config. If output parameter is not
    used, the template file will be edited in-place. Variables in the template
    file can be specified using the following formats: ${plugin:path/to/value}

    For example: ${var:path/to/value} or ${vault:path/to/secret}
    """
    config = Config(
        config_file=config_file,
        default_config=default_config,
        deploy_config=deploy_config,
    )
    config.interpolate_file(template_file=template, destination_file=output)
