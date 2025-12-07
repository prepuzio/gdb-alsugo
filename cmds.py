import gdb
from functools import wraps

import sys
import os

import json
import random
import string

from .treesitter_helper import *
from .ai import *
from .md_helper import *
from .enums import PAYLOAD_FIELDS, QUERY_FIELDS, generate_fields

class Frame:
    def __init__(self, frame=None):
        if frame is None:
            self._frame = gdb.selected_frame()
        else:
            self._frame = frame

    @property
    def funcname(self):
        return self._frame.function().print_name

    @property
    def symbols(self):
        return list(self._symbols())

    @property
    def line(self):
        sal = self._frame.find_sal()
        number = sal.line - 1
        with open(sal.symtab.fullname(), "r") as f:
            return f.readlines()[number]

    @property
    def locals(self):
        return [{ s["print_name"]: s["value"]} 
            for s in self._symbols() 
                if s["is_variable"] == True]

    @property
    def funcbody(self):
        return treesitter_matches(
                frame=self._frame,
                query_field = QUERY_FIELDS["FUNCTION"],
                ).search(self.funcname)

    def _symbols(self):
        for sym in self._frame.block():
            yield { 
                "name": sym.name,
                "linkage_name": sym.linkage_name,
                "print_name": sym.print_name,
                "type": sym.type,
                "addr_class": sym.addr_class,
                "is_variable": sym.is_variable,
                "is_argument": sym.is_argument,
                "is_function": sym.is_function,
                "is_constant": sym.is_constant,
                "symtab": sym.symtab,
                "line": sym.line,
                "name": sym.name,
                "value": str(sym.value(self._frame)) if sym.is_variable or sym.is_constant else None,
            }


Version = dict(
        plugin_name = "gdb-alsugo",
        version = "0.08",
        )
cmds = dict()
convs = dict()

def errorprint(msg):
    print(msg, file=sys.stderr)

def gdb_register(cmds, names):
    def wrap(fn):
        for name in names:
            cmds[name] = fn
        return fn
    return wrap

@gdb_register(cmds, ["ping"])
def ping_cmd(args, from_tty):
    print("pong")

@gdb_register(cmds, ["version"])
def version_cmd(args, from_tty):
    print(json.dumps(Version, indent=2))

@gdb_register(cmds, ["payload", "json"])
def payload_cmd(args, from_tty):
    print(craft_payload(PAYLOAD_FIELDS["ALL"]))

@gdb_register(cmds, ["spiega"])
def spiega_cmd(args, from_tty):
    payload = craft_payload(PAYLOAD_FIELDS["LINE"] | 
                            PAYLOAD_FIELDS["FUNCTION"] |
                            PAYLOAD_FIELDS["BODY"] |
                            PAYLOAD_FIELDS["LOCALS"]
                            )
    md().print(AiClient()
          .query("siamo dentro gdb, descrivi la seguente funzione:" + 
                 str(payload)))

def craft_payload(fields=PAYLOAD_FIELDS["NONE"]):
    payload = {}
    f = Frame()

    if fields & PAYLOAD_FIELDS["LINE"]:
        payload["current_line"] = f.line
    if fields & PAYLOAD_FIELDS["FUNCTION"]:
        payload["current_function"] = f.funcname
    if fields & PAYLOAD_FIELDS["BODY"]:
        payload["current_function_body"] = f.funcbody
    if fields & PAYLOAD_FIELDS["LOCALS"]:
        payload["locals"] = f.locals

    return payload
