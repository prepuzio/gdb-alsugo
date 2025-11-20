import gdb
from functools import wraps
import threading

import sys
import os

import json
import random
import string

Settings = dict

class Cmds():
    def __init__(self):
        # internal register for commands names and what functions they map to
        self._map= {}
        # keep a shared lock for atomic execution
        self._lock = threading.RLock()
        self._convs_ptr = convs

        self._settings = Settings(
                plugin_name = "gdb-alsugo",
                default_command = "status -default_command",
                version = "0.02",
                conversations = [],
                aliases = {},
                current_conversation = None,
                )
    

    def __contains__(self, key):
        return key in self._map

    def __setitem__(self, key, value):
        self._map[key] = value

    def __getitem__(self, key):
        return self._map[key]

    def __update(self):
        self._settings["conversations"] = self._convs_ptr.list
        self._settings["current_conversation"] = self._convs_ptr.get_current()

    @property
    def lock(self):
        return self._lock

    @property
    def settings(self):
        self.__update()
        return self._settings

    @property
    def completions(self):
        aliases = list(self._settings.get('aliases', {}))
        commands = list(self._map.keys())
        return aliases + commands


class Convs():
    def __init__(self):
        self._randname_default_size = 8
        self._list = []
        self._current = None 

    def new(self, value=None):
        self.__append(value)

    def get_current(self):
        return self._current

    def set_current(self, value):
        if not value in self._list:
            raise RuntimeError(f"{value} not in {self._list}")     
        self._current = value

    def __update(self, value=None):
        self.set_current()

    def __append(self, value=None):
        if value == None:
            value = self.__randname()
        if value in self._list:
            raise RuntimeError(f"conv with name {value} already exists!")
        self._list.append(value)

    def __randname(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=self._randname_default_size))

    def __contains__(self, value):
        return value in self._list

    def __getitem__(self, idx):
        return self._list[idx]

    def __len__(self):
        return len(self._list)

    def __str__(self):
        return str(self._list)

    def __repr__(self):
        return f"{self._list!r}"

    @property
    def list(self):
        return self._list

convs = Convs()
cmds = Cmds()

def perror(msg):
    print(msg, file=sys.stderr)

# rename to register_commands
def cmd(names):
    def wrap(fn):
        for name in names:
            cmds[name] = fn
        return fn
    return wrap

def atomic(fn):
    @wraps(fn)
    def wrap(*a, **kw):
        with cmds._lock:
            return fn(*a, **kw)
    return wrap

@cmd(["ping"])
def ping_cmd(args, from_tty):
    print("pong")

@cmd(["new", "nuova"])
@atomic
def new_cmd(args, from_tty):
    convs.new()
    print(convs)

@cmd(["status", "info"])
def status_cmd(args, from_tty):
    settings = cmds.settings
    settings = dict_mask(cmds.settings, args)
    print(json.dumps(settings, indent=2))

def dict_mask(dictionary, args):
    strip = lambda k: k[1:]

    new_dict = dictionary.copy()
    explicit = {}

    for arg in args:
        remove = arg[0] == '-'
        add = arg[0] == '+'
        stripped = strip(arg)
        if remove:
            if explicit.pop(stripped, False) is False:
                new_dict.pop(stripped, None)
        elif add:
            if explicit:
                explicit[stripped] = dictionary[stripped]
            new_dict[stripped] = dictionary[stripped]
        else: # default: 
            explicit[arg] = dictionary[arg]

    if explicit: 
        return explicit
    else:
        return new_dict

# FINE CODICE
@cmd("json")
def context2json(argv, from_tty):
    data = {
            "context_lines": line_text(context=5),
            "current_line": line_text()[0],
            "line_number": line_number(),
            "loaded_libaries": get_libs(),
            }
    print(json.dumps(data))

def line_number():
    return get_sal().line

def line_text(context: int = 0, number: int = 0):
    if number == 0:
        number = line_number() - 1
    start = max(0, number - context//2)
    end = number + 1 + context//2 
    sal = get_sal()

    with open(sal.symtab.fullname(), "r") as f:
        return [line.rstrip('\n') for line in f.readlines()[start:end]]

def get_sal():
    return gdb.selected_frame().find_sal()

def get_libs():
    return [obj.filename for obj in gdb.objfiles()]
