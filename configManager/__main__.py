import sys, json
from configManager import config

helpText = """
Usage: python3 -m configManager [get|insert|build|overlay|dump|help]

get     [config.ini group key]       Get a single value from a config file.
insert  [config.ini group key value] Add or update a key/value pair to group in the specified INI file. If group does not yet exist, it will be created.
build   [config.ini template output] Import config from `file1`; interpolate `file2`; output `file3`.
overlay [inputConfig.ini config.ini] Pull values from incomingConfig into config.
dump    [config.ini]                 Export instantiated config as JSON.
help                                 Prints this help text.
"""

if len(sys.argv) < 2:
    print(helpText)
    exit()
if sys.argv[1] == "get":
    config.load(sys.argv[2])
    group = sys.argv[3]
    key = sys.argv[4]
    print(config.get(group, key), end="")
elif sys.argv[1] == "insert":
    config.load(sys.argv[2])
    group = sys.argv[3]
    key = sys.argv[4]
    value = ' '.join(sys.argv[5:len(sys.argv)])
    config.set(group, key, value)
    config.save()
elif sys.argv[1] == "build":
    config.load(sys.argv[2])
    config.interpolateFile(sys.argv[3], sys.argv[4])
elif sys.argv[1] == "overlay":
    config.load(sys.argv[3])
    config.load(sys.argv[2])
    config.save(sys.argv[3])
elif sys.argv[1] == "dump":
    config.load(sys.argv[2])
    print(json.dumps(config.export(), indent=2))
else:
    print(helpText)
