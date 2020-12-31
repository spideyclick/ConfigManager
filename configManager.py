import re

class ConfigManager():
    """
    ConfigManager is an object to represent the data contained in one or more
    .ini files. The goal is to safely read and write configuration data while
    allowing for more robust interpolation than the default Python ConfigParser
    library.
    """

    def __init__(self, commentPrefixes=[';', '#', '/']):
        self.commentPrefixes = commentPrefixes
        self.patterns = {
            'group': r"^\[(.+)\]$",
            'entry': r"^([\S]*)[ ]?=[ ]?(.*)$",
            'interpolation': r"\${([^:]*):([^}]*)}",
        }
        self.plugins = {}
        self.groups = []
        self.entries = {}

    def importConfigFile(self, configFile):
        """
        Open a configuration file (.ini format expected) and import
        configurations into the ConfigManager object (ConfigManager.groups and 
        ConfigManager.entries).
        """
        with open(configFile, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue
                elif line[0] in self.commentPrefixes:
                    continue
                elif re.match(self.patterns['group'], line):
                    self.groups.append(re.sub(
                        self.patterns['group'], '\\1', line))
                elif re.match(self.patterns['entry'], line):
                    thisGroup = self.groups[-1]
                    if thisGroup not in self.entries.keys():
                        self.entries[thisGroup] = {}
                    key = re.sub(self.patterns['entry'], '\\1', line)
                    value = re.sub(self.patterns['entry'], '\\2', line)
                    self.entries[thisGroup][key] = value

    def updateConfigFile(self, configFile):
        """
        Write configurations to an existing configuration file. Only updates
        entries that already exist in the given configuration file--new groups
        and entries will not be added.
        """
        newFile = """"""
        currentGroup = ""
        entriesFound = []
        with open(configFile, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if re.match(self.patterns['entry'], line):
                    if not currentGroup:
                        print("Key <{0}> not found in any Group..".format(key))
                        newFile += line + "\n"
                        continue
                    if currentGroup in self.entries.keys():
                        line = line.strip()
                        key = re.sub(self.patterns['entry'], '\\1', line)
                        entriesFound.append(key)
                        if key not in self.entries[currentGroup].keys():
                            print("Key <{0}> not found in Group <{1}>.".format(
                                key, currentGroup))
                            newFile += line + "\n"
                            continue
                        value = self.entries[currentGroup][key]
                        newFile += "{0} = {1}\n".format(key, value)
                        continue
                    newFile += line + "\n"
                    continue
                elif re.match(self.patterns['group'], line):
                    thisGroup = re.sub(self.patterns['group'], '\\1', line)
                    if not currentGroup:
                        newFile += line + "\n"
                        currentGroup = thisGroup
                        continue
                    if currentGroup not in self.groups:
                        newFile += line + "\n"
                        currentGroup = thisGroup
                        continue
                    if len(entriesFound) < len(self.entries[currentGroup].keys()):
                        for entry in self.entries[currentGroup].items():
                            if entry[0] not in entriesFound:
                                newFile += "{0} = {1}\n".format(
                                    entry[0], entry[1])
                        newFile += "\n"
                    currentGroup = thisGroup
                    newFile += line + "\n"
                else:
                    newFile += line + "\n"
        with open(configFile, 'w') as f:
            f.write(newFile)

    def interpolateFile(self, inputFile, outputFile=None):
        """
        Takes a given file and searches for all matches to the interpolation
        pattern. i.e. ${group.value}

        Once the entire file has been scanned for interpolation patterns,
        all those patterns are replaced if there is a matching entry or
        interpolation method in the ConfigManager object.
        
        Changes are then written in-place to disk.

        Args:
            inputFile (string): File to Process, should contain references to
            config in the same interpolation format as .ini files
            i.e. ${group:key}

            outputFile (string, optional): The output file to write interpolated
            lines to. If not specified, it will be assumed the input file is
            also the output file.
        """

        newFile = """"""
        if not outputFile:
            outputFile = inputFile
        with open(inputFile, 'r') as f:
            for line in f.readlines():
                for match in re.finditer(self.patterns['interpolation'], line):
                    variable = match.group(0)
                    group = match.group(1)
                    key = match.group(2)
                    value = self.get(group, key)
                    line = line.replace(variable, value)
                newFile += line
        with open(outputFile, 'w') as f:
            f.write(newFile)

    def _splitValue(self, value):
        """Splits a value on space, pipe or comma. Intended to split
        configurations specified as an array into separarte values using these
        characters.

        Args:
            value (string): The value to be split.

        Returns:
            list: The split values
        """
        return list(filter(None, re.split(' |,', value)))

    def interpolate(self, value):
        """
        Takes a value and interpolates the references to other fields and
        functions, returning a fully rendered value.
        """
        newValue = value
        for entry in re.finditer(self.patterns['interpolation'], value):
            result = ""
            interpolationText = value[entry.start():entry.end()]
            operation = re.sub(
                self.patterns['interpolation'], '\\1', interpolationText)
            initialValue = re.sub(
                self.patterns['interpolation'], '\\2', interpolationText)
            if operation in self.plugins.keys():
                result = self.plugins[operation].get(initialValue)
                # result = "Not yet implemented"
            elif operation in self.groups:
                if initialValue in self.entries[operation].keys():
                    result = self.entries[operation][initialValue]
            else:
                result = "ConfigManager: Interpolation Method/Path not found"
            newValue = newValue.replace(interpolationText, result)
        return newValue

    def add(self, group, key, value):
        """
        Add a key/value pair to specified group within the configuration object.
        If group object does not yet exist, it will be created.
        """
        if group not in self.groups:
            self.groups.append(group)
            self.entries[group] = {}
        self.entries[group][key] = value

    def get(self, group, key, format=None):
        """
        Gets a value by group and key, splitting by spaces and/or commas if
        format='array'. Also calls interpolate on any fields with references
        detected.
        """
        value = self.entries[group][key]
        if re.search(self.patterns['interpolation'], value):
            value = self.interpolate(value)
        if format == "array":
            return self._splitValue(value)
        return value

    def export(self):
        """
        Returns all entries.
        """
        return self.entries

if __name__ == "__main__":
    import sys
    config = ConfigManager()
    if len(sys.argv) > 1:
        if sys.argv[1] == "get":
            config.importConfigFile(sys.argv[2])
            group = sys.argv[3]
            key = sys.argv[4]
            print(config.get(group, key), end="")
        elif sys.argv[1] == "insert":
            group = sys.argv[3]
            key = sys.argv[4]
            value = ' '.join(sys.argv[5:len(sys.argv)])
            config.add(group, key, value)
            config.updateConfigFile(sys.argv[2])
        elif sys.argv[1] == "build":
            config.importConfigFile(sys.argv[2])
            config.interpolateFile(sys.argv[3], sys.argv[4])
        elif sys.argv[1] == "import":
            config.importConfigFile(sys.argv[3])
            config.updateConfigFile(sys.argv[2])
