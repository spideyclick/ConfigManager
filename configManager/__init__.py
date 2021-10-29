import re, requests, json

### Helper Functions

def merge(source, destination):
    """Recursively merge dictionaries."""
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

def safeJson(result, path=[]):
    """Take the result of a requests call and format it into a structured dict."""
    if result.status_code != 200:
        output = {'code': result.status_code, 'content': result.text}
        print("ConfigManager: get secret failed (token expired?)")
        print(json.dumps(output, indent=2))
        return output
    output = result.json()
    if path:
        for level in path:
            try:
                output = output[level]
            except:
                return {'code': 200, 'content': "path not found: {0}".format(path)}
    return output

def checkToken(f):
    """Wrap function; if it fails, run it again with argument renewToken=True"""
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            return f(*args, **kwargs, renewToken=True)
    return wrapper

### Main class definition

class ConfigManager():
    """
    ConfigManager is an object to represent the data contained in one or more
    .ini files. The goal is to safely read and write configuration data while
    allowing for more robust interpolation than the default Python ConfigParser
    library.

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
    """

    def __init__(self, sourceFile=None, commentPrefixes=[';', '#', '/']):
        self.sourceFile = sourceFile
        self.commentPrefixes = commentPrefixes
        self.patterns = {
            'group': r"^\[(.+)\]$",
            'entry': r"^([\S]*)[ ]*=[ ]*(.*)$",
            'interpolation': r"\${([^:]*):([^}]*)}",
        }
        self.entries = {}

    def load(self, sourceFile=None):
        """
        Open a configuration file (.ini format expected) and import
        configurations into the ConfigManager object (ConfigManager.groups and
        ConfigManager.entries).
        """
        if sourceFile:
            self.sourceFile = sourceFile
        assert self.sourceFile is not None
        merge(self.fileToRawEntries(sourceFile), self.entries)

    def fileToRawEntries(self, file):
        output = {}
        currentGroup = None
        with open(file, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue
                elif line[0] in self.commentPrefixes:
                    continue
                elif re.match(self.patterns['group'], line):
                    currentGroup = re.sub(self.patterns['group'], '\\1', line)
                    if currentGroup not in output.keys():
                        output[currentGroup] = {}
                elif re.match(self.patterns['entry'], line):
                    key = re.sub(self.patterns['entry'], '\\1', line)
                    value = re.sub(self.patterns['entry'], '\\2', line)
                    output[currentGroup][key] = value
        return output

    def save(self, destinationFile=None):
        """
        Write configurations to an existing configuration file. Only updates
        entries that already exist in the given configuration file--new groups
        and entries will not be added.
        """
        assert self.sourceFile is not None
        if not destinationFile:
            destinationFile = self.sourceFile
        newFile = """"""
        currentGroup = None
        entriesFound = []
        groupsFound = []
        with open(destinationFile, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if re.match(self.patterns['entry'], line):
                    if currentGroup in self.entries.keys():
                        key = re.sub(self.patterns['entry'], '\\1', line)
                        entriesFound.append(key)
                        if key not in self.entries[currentGroup].keys():
                            newFile += f'{line}\n' # Union: group ++; key -+
                            continue
                        value = self.entries[currentGroup][key]
                        newFile += f'{key} = {value}\n'
                    else:
                        newFile += f'{line}\n' # Union: group -+; key -+
                elif re.match(self.patterns['group'], line):
                    thisGroup = re.sub(self.patterns['group'], '\\1', line)
                    groupsFound.append(thisGroup)
                    if not currentGroup:
                        newFile += f'{line}\n'
                        currentGroup = thisGroup
                        continue
                    if currentGroup not in self.entries.keys():
                        newFile += f'{line}\n' # Union: group -+
                        currentGroup = thisGroup
                        continue
                    for key, value in self.entries[currentGroup].items():
                        if key not in entriesFound:
                            newFile += f'{key} = {value}\n' # Union: group ++; key +-
                    entriesFound = []
                    currentGroup = thisGroup
                    newFile += f'{line}\n'
                else: # Comments, blank lines, etc.
                    newFile += f'{line}\n'
            for key, value in self.entries[currentGroup].items():
                if key not in entriesFound:
                    newFile += f'{key} = {value}\n' # Union: group ++; key +-
        for group in self.entries.keys():
            if group not in groupsFound:
                newFile += f'[{group}]\n' # Union: group +-
                for key, value in self.entries[group].items():
                    newFile += f'{key} = {value}\n' # Union: group +-; key +-
        with open(destinationFile, 'w') as f:
            f.write(newFile)

    def interpolateFile(self, templateFile, destinationFile=None):
        """
        Takes a given file and searches for all matches to the interpolation
        pattern.

        Once the entire file has been scanned for interpolation patterns,
        all those patterns are replaced if there is a matching entry or
        interpolation method in the ConfigManager object.
        
        Changes are then written in-place to disk.

        Args:
            templateFile (string): Path to file that will be processed. Should
            contain references to config in the same interpolation format as
            .ini files (i.e. ${group:key})

            destinationFile (string, optional): Path to the output file to write
            interpolated lines to. If not specified, it will be assumed the
            input file is also the output file.
        """
        if not destinationFile:
            destinationFile = templateFile
        newFile = """"""
        with open(templateFile, 'r') as f:
            for line in f.readlines():
                for match in re.finditer(self.patterns['interpolation'], line):
                    variable = match.group(0)
                    group = match.group(1)
                    key = match.group(2)
                    value = self.get(group, key)
                    assert type(value) is str
                    line = line.replace(variable, value)
                newFile += line
        with open(destinationFile, 'w') as f:
            f.write(newFile)

    def _splitValue(self, value):
        """
        Splits a value on space, pipe or comma.
        Intended to split configurations specified as an array into separate
        values using these characters.
        """
        return list(filter(None, re.split(' |,', value)))

    def get(self, group, key, format=None):
        """
        Gets a value by group and key, interpolating variables and secrets.
        Split by spaces and/or commas if format='array'.
        """
        if group not in self.entries.keys():
            raise KeyError(f'ConfigManager: group {group} not found')
        if key not in self.entries[group]:
            raise KeyError(f'ConfigManager: key {key} not found in group {group}')
        value = self.entries[group][key]
        if re.search(self.patterns['interpolation'], value):
            value = self.interpolate(value)
        if format == "array":
            return self._splitValue(value)
        return value

    def interpolate(self, value):
        """
        Takes a value and interpolates the references to other fields and
        functions, returning a fully rendered value.
        """
        newValue = value
        for entry in re.finditer(self.patterns['interpolation'], value):
            result = ""
            interpolationText = value[entry.start():entry.end()]
            source = re.sub(self.patterns['interpolation'], '\\1', interpolationText)
            initialValue = re.sub(self.patterns['interpolation'], '\\2', interpolationText)
            if source == 'secret':
                result = self.getSecret(initialValue)
            else:
                result = self.get(source, initialValue)
            newValue = newValue.replace(interpolationText, result)
        return newValue

    @checkToken
    def getSecret(self, secret, renewToken=False):
        """Get a secret from a Hashicorp Vault secrets manager."""
        token = self.get('secrets', 'token')
        if not token or renewToken:
            self.renewToken()
            token = self.get('secrets', 'token')
        path = '/'.join(secret.split('/')[0:-1])
        secret = secret.split('/')[-1]
        result = safeJson(requests.get(
            self.get('secrets', 'address') + path,
            headers = {"X-Vault-Token": token},
        ), ['data', 'data'])
        return result[secret]

    def renewToken(self):
        """Get or renew a token from the Hashicorp Vault API."""
        print('ConfigManager: getting new secrets token')
        response = requests.post(
            f'{self.get("secrets", "address")}auth/approle/login',
            data = json.dumps({
                "role_id": self.get("secrets", "role"),
                "secret_id": self.get("secrets", "secret")
            }),
        )
        self.entries['secrets']['token'] = safeJson(response, ['auth', 'client_token'])
        self.save()
        print('ConfigManager: new secrets token saved')

    def set(self, group, key, value):
        """
        Sets a value by group and key, parsing arrays and objects as needed.
        Creates group and key if either does not exist.
        """
        if (type(value).__name__ in ['list', 'tuple', 'dict']):
            value = json.dumps(value)
        if group not in self.entries.keys():
            self.entries[group] = {}
        self.entries[group][key] = value

    def export(self):
        """Returns all entries."""
        output = {}
        for group in self.entries.keys():
            output[group] = {}
            for entry in self.entries[group].keys():
                output[group][entry] = self.get(group, entry)
        return output

config = ConfigManager()
