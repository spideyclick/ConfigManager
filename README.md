# ConfigManager

ConfigManager is a Python library built to make configurations easy to deal with while extending their functionality. The goal is to safely read and write configuration data while allowing for interpolation and secret management.

## Main Features

- Supports `.ini`, `.json` and `.yaml` file formats
- Configurations can use the `${plugin:path}` syntax
    - Hashicorp Vault Plugin is included to make secrets easy
    - Extendible with custom plugins
- Command-line interface allows library to be used outside of Python

## Installation

Install library as a PIP package:

```sh
pip install git+https://gitlab.midwestholding.dev/midwest-holding-developers/configmanager.git@v2.0.0
```

Or list in your `requirements.txt`:

```sh
config_manager @ git+https://gitlab.midwestholding.dev/midwest-holding-developers/configmanager.git@v2.0.0
```

## Usage

First, you'll need a configuration file to save and load entries ([full example below](#example-config-file)):

```yaml
# my-config.yaml
test_group:
  str: "abc"
  int: 123
  bool: true
  array:
  - "red"
  - "green"
  - "blue"
```

This can then be accessed using the python module:

```py
from config_manager import Config
config = Config("my-config.yaml")
print(config.get("test_group/int"))

# 123
```

Alternatively, you can call the configManager module from a shell script with `python -m config_manager`:

```sh
echo "The value is: $(python -m config_manager get -c my-config.yaml test_group/int)"

# The value is: 123
```

Run `python -m config_manager --help` for full command-line documentation.

## Main Functions

- `config = Config("my-config.yaml")`: Load a configuration and optional `default_config` and `deploy_config` files.
  - `default_config`: This is a read-only configuration that can contain all default values. This file will never be changed.
  - `deploy_config`: This file can be used to overlay the main config file. Like the default config, it is also not modified.
- `get("path/to/config")`: Gets a value by `path` string, interpolating variables and secrets. When using this function, there are no guarantees about the type. It is recommended to use one of the following:
  - `get_str`
  - `get_int`
  - `get_float`
  - `get_bool`
- `set("path/to/config", "value")`: Sets a value by path
- `interpolate_file(Path("template_file"), Path("output_file"))`: Takes a template file and an output file and replaces all variable references with values from the loaded config.

## ConfigManager's Role in Deployment

```sh
── yourApp/
   ├── deploy/
   │   └── config.json        # Should contain all of the actual deployment-specific configurations
   ├── run.sh                 # This should contain the import logic (example below)
   ├── setup/
   │   └─ default-config.json # Tracked in Git
   └── config.json            # Not tracked in git
```

1. Start identifying configurations that:
    - You would like to change when deploying (testing, production, other environments)
    - OR are secrets you'd prefer not to store in plain text using the Vault plugin
2. Create a `default-config.json` file. This file should contain only defaults for your project and **should not contain any secrets**. It should contain all the paths that `config.json` file has, but with either empty or example values entered.
3. Create a `config.json` file. This is the one configManager is actually going to be reading from and writing to. Add `config.json` to your `.gitignore` file. `config.json` should **not** be tracked by git! You want to keep your non-default configurations separate from your project.
4. (Optional) If you're mounting a `deploy` folder with Docker, you'll want a separate `config.json` file that contains all the settings from that specific deployment. These values will be loaded on top of whatever configurations are found in the existing configuration.
5. Start replacing configurations in your code with ConfigManager calls!

## Variables

ConfigManager allows for variables to be used in a value, whether stored in INI, JSON or YAML. Variables are denoted in a specific format: `${plugin:path}`.

```yaml
database:
    host: hostname_here
    port: 5432
    combined_value: ${var:database/host}:${var:database/port}
```

This would result in `combined_value` having the value of `hostname_here:5432` when called with `config.get("database/combined_value")`.

## Secret Configurations with Hashicorp Vault

ConfigManager can work with a Hashicorp Vault instance to gather secrets at runtime. By using the `vault` plugin syntax, you can specify the location of a secret, so long as you have a properly configured `secrets` section in your config:

```json
{
    "main": {
        "my_secret": "${vault:kv/data/path/to/secret}",
        "combined_value": "abc-${vault:kv/data/path/to/another/secret}-xyz"
    },
    "secrets": {
        "address": "https://vault.your_domain.com/v1/",
        "role_id": "your_role_id",
        "secret_id": "your_secret_id"
    }
}
```

This requires you to have a working Hashicorp Vault instance running somewhere with `appRole` access enabled. You will also need a policy, role, appId and appSecret created (see the next section).

## Hashicorp Vault App Roles

<https://learn.hashicorp.com/tutorials/vault/approle>

1. Create a [policy](https://www.vaultproject.io/docs/concepts/policies) for an app using the Web UI.
2. Create an [appRole](https://www.vaultproject.io/docs/auth/approle) and attach policy
   - Replace `appName` and `token_policies`
   - Both `bound_cidrs` are optional. If you want to restrict the app to getting secrets from only one or a range of IP addresses, that's how you can do it.

```sh
vault write auth/approle/role/<appName> \
    token_policies="policy1, policy2" \
    token_ttl=1h \
    token_max_ttl=4h \
    secret_id_bound_cidrs="8.8.8.8/32" \
    token_bound_cidrs="8.8.8.8/32"
```

3. Get Role ID (save to config as `vault/role_id`): `vault read auth/approle/role/[your_app_name]/role-id`
4. Set/get Secret ID (save to config as `vault/secret_id`): `vault write -force auth/approle/role/[your_app_name]/secret-id`

## Example INI Config File

> Remember, you can use JSON or YAML formats if you'd prefer!

```ini
# This is just an example file.
# This should customized before use in your project.

[main]
debug = False
primaryDomain = yourdomain.com
externalPort = 80

[server]
secretKey = null
allowedHosts = localhost, ${main:primaryDomain}

[auth]
oauth_app_id = ${secret:kv/data/yourapp/oauth/app_id}
oauth_app_secret = ${secret:kv/data/yourapp/oauth/app_secret}
oauth_authority = https://login.microsoftonline.com/${secret:kv/data/yourapp/oauth/tenant_id}
oauth_redirect = https://${main:primaryDomain}:${main:externalPort}/callback

[database]
address = 0.0.0.0
port = 55555
password = ${secret:kv/data/yourapp/db/password}

[aws]
region = ${secret:kv/data/yourapp/aws/region}
access_key_id = ${secret:kv/data/yourapp/aws/key_id}
secret_access_key = ${secret:kv/data/yourapp/aws/key}

[secrets]
address = https://vault.yourdomain.com/v1/
role = yourRoleId
secret = yourSecretId
```
