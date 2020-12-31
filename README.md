# ConfigManager

ConfigManager is a Python library built to make INI configurations easy to deal with while extending their functionality. The goal is to safely read and write configuration data while allowing for more robust interpolation than the default Python ConfigParser library.

What's wrong with the existing ConfigParser library?

- It was assuming interpolation on values I was not intending to interpolate (any value containing curly brackets)
- It was manipulating my config file, removing all comments
    - Unless put into raw mode and specifying a different comment prefix, which actually ends up storing your comments as configurations, which I am very uncomfortable with.
- ConfigParser decides what data type to return based on the value, leading to data types changing from user input, which is also a no-no in my book.
- Finally, extending configurations with an external library like Vault will be a lot easier of a task with a custom interpolation parser.

## Usage

*How do I start using ConfigManager in my Python project?*

1. Copy the ConfigManager library to a folder in your project (usually `lib`). You'll probably want to grab the Vault library too.
2. Start identifying configurations that:
  - you would like to change when deploying (testing, production, other environments)
OR
  - are secrets you'd prefer not to store in plain text (with the help of a plugin like Vault)
3. Create a couple INI files in your project's root directory: defaultConfig.ini and config.ini.
  - Add `config.ini` to your `.gitignore` file. `config.ini` should NOT be tracked by git! You want to keep your configurations separate from your project.
  - `defaultConfig.ini` SHOULD be added to your project in git, and it should be a generic representation of what someone may want to put into the config file. It should contain all the groups and keys the `config.ini` file has, but with either empty or example values entered.
4. Start replacing configurations in your code with ConfigManager calls.
    ```py
    from lib import configManager
    config = configManager.ConfigManager()
    config.importConfigFile('config.ini')
    MY_SETTING = config.get('groupName', 'settingName')
    ```

> Note: data types are not recorded. ConfigManager will always return a string.

## Extending INI Files

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

In the future, I would like to implement plugins as well, so that instead of looking for a variable, the program runs a function (for example calling another library to get a value). This has not yet been implemented.

## Using ConfigManager for Deployment

There are a few bindings for calling ConfigManager outside of a Python script:

### `get`

Get a single value from a config file.

`python lib/configManager.py get config.ini group key`

This can be used to load variables in shell or bash commands:

`python ./manage.py runserver 0.0.0.0:$(python lib/configManager.py get config.ini main port)`

### `insert`

Add or update a `key`/`value` pair to `group` in the specified INI file. If `group` does not yet exist, it will be created.

`python lib/configManager.py insert config.ini group key value`

### `build`

Import config from `file1`; interpolate `file2`; output `file3`.

`python lib/configManager.py build file1 file2 file3`

`python lib/configManager.py build config.ini /app/setup/nginx.conf /etc/nginx/nginx.conf`

### `import`

Import file2 into file1.

- Adds any groups and/or keys present in file2 that are missing in file1.
- Uses keys from file2 to update keys in file1 if there are conflicts.

`python lib/configManager.py import config.ini deploy/config.ini`
