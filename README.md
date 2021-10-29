# ConfigManager

ConfigManager is a Python library built to make INI configurations easy to deal with while extending their functionality. The goal is to safely read and write configuration data while allowing for more robust interpolation than the default Python ConfigParser library.

What's wrong with the existing ConfigParser library?

- It was assuming interpolation on values I was not intending to interpolate
(any value containing curly brackets)
- It was manipulating my config file, removing all comments
    - Unless put into raw mode and specifying a different comment prefix,
    which actually ends up storing your comments as configurations, which I
    am very uncomfortable with.
- ConfigParser decides what data type to return based on the value, leading
to data types changing from user input, which is also a no-no in my book.
- Finally, extending configurations will be a lot easier of a task with a
custom interpolation parser.

## Installation

Install library as a PIP package:

```sh
pip install git+https://github.com/spideyclick/ConfigManager@v1.0.1
```

## Usage

First, you'll need a `.ini` file to save and load entries ([full example below](#example-config-file)):

```ini
[main]
sampleKey = sampleValue
```

This can then be accessed using the python module:

```py
from configManager import config
config.importConfigFile('config.ini')
print(config.get('main', 'sampleKey'))
```

Alternatively, you can call configManager from a script ([full example below](#example-server-startup-script)):

```sh
echo "The value is: $(python -m configManager get config.ini main sampleKey)"
```

## Methods

- `export()`: Returns all entries.
- `get(group, key, format)`: Gets a value by `group` and `key`, interpolating variables and secrets. Split by spaces and/or commas if `format='array'`.
- `interpolateFile(templateFile, destinationFile=None)`: Takes a given file and searches for all matches to the interpolation pattern. Once the entire file has been scanned for interpolation patterns, all those patterns are replaced if there is a matching entry or interpolation method in the ConfigManager object. Changes are then written in-place to disk.
    - `templateFile` (string): Path to file that will be processed. Should contain references to config in the same interpolation format as .ini files (i.e. ${group:key}).
    - `destinationFile` (string, optional): Path to the output file to write interpolated lines to. If not specified, it will be assumed the input file is also the output file.
- `load(sourceFile=None)`: Open a configuration file (.ini format expected) and import configurations into the ConfigManager object (ConfigManager.groups and ConfigManager.entries). `sourceFile` is remembered and will be used by default for subsequent `load` and `save` calls.
- `save(destinationFile=None)`: Write configurations to an existing configuration file. Only updates entries that already exist in the given configuration file - new groups and entries will not be added. `destinationFile` can be specified if desired output file is different from what was most recently loaded.
- `set(group, key, value)`: Sets `value` under `group` and `key`, parsing arrays and objects as needed. Creates `group` and `key` if either does not exist.

## Scripting Operations

These can be used in a server startup script. [See example below](#example-server-startup-script).

```
get     [config.ini group key]       Get a single value from a config file.
insert  [config.ini group key value] Add or update a key/value pair to group in the specified INI file. If group does not yet exist, it will be created.
build   [config.ini template output] Import config.ini; interpolate template and save to output.
overlay [inputConfig.ini config.ini] Pull values from inputConfig into config.
dump    [config.ini]                 Export instantiated config as JSON.
help                                 Prints this help text.
```

## ConfigManager's Role in Deployment

```sh
── yourApp/
   ├── deploy/
   │   └── config.ini    # Should contain all of the actual deployment-specific configurations
   ├── run.sh            # This should contain the import logic (example below)
   ├── defaultConfig.ini # Tracked in Git
   └── config.ini        # Not tracked in git
```

1. Start identifying configurations that:
    - You would like to change when deploying (testing, production, other environments)
    - OR are secrets you'd prefer not to store in plain text using the Vault plugin
2. Create a `defaultConfig.ini` file. This file should contain only defaults for your project and **should not contain any secrets**. It should contain all the groups and keys the `config.ini` file has, but with either empty or example values entered.
3. Create a `config.ini` file. This is the one configManager is actually going to be reading from and writing to. Add `config.ini` to your `.gitignore` file. `config.ini` should **not** be tracked by git! You want to keep your non-default configurations separate from your project.
4. (Optional) If you're mounting a `deploy` folder with Docker, you'll want a separate `config.ini` file that contains all the settings from that specific deployment. The server startup script for you project should call the `build` sccript operation to deploy those configurations on top of whatever `config.ini` file already exists inside the container.
5. Create or modify your server's startup script to handle creating `config.ini`, then importing `defaultConfig.ini` then `deploy/config.ini` into it. [See example below](#example-server-startup-script).
6. Start replacing configurations in your code with ConfigManager calls.

> Note: data types are not recorded. ConfigManager will always return a string unless specified otherwise via the format parameter of the `get` method.

## Variables

INI files follow a pretty simple format: blank lines, `[group]` lines and `key = value` lines. Comments must be on a line of their own and that line must start with a semicolon (`;`).

Those are pretty standard INI rules, but ConfigManager allows for variables to be used in a value. Variables are denoted in a specific format: `${group:key}`.

```ini
[group1]
key1 = abc
key2 = def

[group2]
combinedKey = ${group1:key1}uvw${group1:key2}xyz
```

This would result in `combinedKey` having the value of `abcuvwdefxyz` when called with `ConfigManager.get('group2', 'combinedKey')`.

## Secret Configurations with Hashicorp Vault

ConfigManager can work with a Hashicorp Vault instance to gather secrets at runtime. By using a special syntax, you can specify the location of a secret, so long as you have a properly configured `[secrets]` section in your config:

```ini
[secrets]
address = https://vault.yourdomain.com/v1/
role = yourRoleId
secret = yourSecretId
token = 

[group1]
key1 = ${secret:kv/data/path/to/secret}
key2 = abc${secret:kv/data/path/to/secret2}def
```

> Note: you can leave `token` blank, since that value will be filled by configManager.

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

3. Get Role ID (save to config!): `vault read auth/approle/role/<appName>/role-id`
4. Set/get Secret ID (save to config!): `vault write -force auth/approle/role/<appName>/secret-id`

## Example Config File

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
token = 
```

## Example Server Startup Script

```sh
#!/bin/bash

# This is just an example file.
# This should be customized before use in your project.

### LOAD DEPLOYMENT FILES

if ! test -f config.ini; then
    cp defaultConfig.ini config.ini
fi
if test -f deploy/config.ini; then
    python -m configManager overlay deploy/config.ini config.ini
fi

### LOAD DOCKER RUN ARGUMENTS INTO CONFIG

args=("$@")
ELEMENTS=${#args[@]}

for (( j=0;j<$ELEMENTS;j++)); do
    THISVALUE=""
    THISKEY=""
    keyAssigned=false
    IFS=\=; read -ra ADDR <<<"${args[${j}]}"
    for i in "${ADDR[@]}"; do
        case $keyAssigned in
            true) THISVALUE="${i}" ;;
            false) THISKEY="${i}" ; keyAssigned=true ;;
        esac
    done
    GROUP=$(sed -E 's/\.\S+//g' <<< $THISKEY)
    KEY=$(sed -E 's/\S+\.//g' <<< $THISKEY)
    python -m configManager insert config.ini ${GROUP} ${KEY} ${THISVALUE}
done

### LOAD APP VERSION VARIABLE

# Load app version into config if this is a development container
if [ -d ".git" ]; then
    python -m configManager insert config.ini main appVersion "$(git describe --tags --long) branch $(git rev-parse --abbrev-ref HEAD) $(git log -1 --format=%ai `git describe --tags`)"
fi

# Load app version into config from system variable.
if [ ! -z "${APP_VERSION}" ]; then
    python -m configManager insert config.ini main appVersion ${APP_VERSION}
fi

### DEPLOY TEMPLATE FILES

python -m configManager build config.ini /app/setup/nginx.conf /etc/nginx/sites-available/nginx.conf
python -m configManager build config.ini /app/setup/aws/config /root/.aws/config
python -m configManager build config.ini /app/setup/aws/credentials /root/.aws/credentials

### START SERVER

python ./manage.py makemigrations
python ./manage.py migrate

/etc/init.d/nginx restart
uwsgi --ini config.ini
```
