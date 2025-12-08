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
    def file(self):
        return self._frame.find_sal().symtab.fullname()

    @property
    def lang(self):
        return self._frame.language()

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

    @property
    def backtrace(self):
        bt = []
        frame = self._frame
        while frame:
            try:
                fn = frame.function()
                name = fn.print_name if fn else "??"
            except:
                name = "??"
            bt.append(name)
            frame = frame.older()
        return bt

    @property
    def regs(self):
        r = {}
        try:
            arch = self._frame.architecture()
            for reg in arch.registers("general"):
                val = self._frame.read_register(reg)
                r[reg.name] = str(val)
        except:
            pass
        return r

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
        version = "0.09",
        )
cmds = {}
convs = {}

class PayloadHelper:
    def __init__(self):
        self._mask = PAYLOAD_FIELDS["LINE"] | PAYLOAD_FIELDS["FUNCTION"] | PAYLOAD_FIELDS["BODY"] | PAYLOAD_FIELDS["LOCALS"]

    def set_mask(self, mask):
        if mask < 0:
            errorprint("invalid mask")
            return
        self._mask = mask

    @property
    def mask(self):
        return self._mask

payload_helper = PayloadHelper()

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
    if not args:
        print(craft_payload(payload_helper.mask))

@gdb_register(cmds, ["mask"])
def mask_cmd(args, from_tty):
    old = payload_helper.mask
    if not args:
        print("PAYLOAD:")
        print(craft_payload(payload_helper.mask))
        return
    
    m = payload_mask(args)
    if m < 0:
        m = payload_helper.mask

    payload_helper.set_mask(m)
    if old != m:
        print("old mask:")
        print_mask( old )

    print("new mask:")
    print_mask( payload_helper.mask )

def print_mask(mask):
    for key in PAYLOAD_FIELDS.keys():
        if key in ("ALL", "NONE"):
            continue
        if mask & PAYLOAD_FIELDS[key]:
            print(key)

@gdb_register(cmds, ["spiega"])
def spiega_cmd(args, from_tty):
    # TODO move craft_payload to PayloadHelper
    payload = craft_payload( payload_helper.mask )
    md().print(AiClient()
          .query("siamo dentro gdb, cio che sta avvenendo" + 
                 "\n\nContext:\n" +
                 json.dumps(payload, indent=2)))

@gdb_register(cmds, ["chiedi", "ask", "addumann"])
def chiedi_cmd(args, from_tty):
    query = input("chiedi: ")
    payload = craft_payload(payload_helper.mask)
    md().print(AiClient()
          .query(query + "\n\nContext:\n" + json.dumps(payload, indent=2)))


def payload_mask(args):
    sane = lambda arg: arg.upper().strip("-").strip("+")

    mask = payload_helper.mask
    for arg in args:
        if not sane(arg) in PAYLOAD_FIELDS.keys():
            errorprint(f"can't find field: {arg}")
            return -1

        if arg.startswith("-"):
            mask &= ~PAYLOAD_FIELDS[sane(arg)]
        else: 
            mask |= PAYLOAD_FIELDS[sane(arg)]
            
    return mask


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
    if fields & PAYLOAD_FIELDS["FILE"]:
        payload["file"] = f.file
    if fields & PAYLOAD_FIELDS["BACKTRACE"]:
        payload["backtrace"] = f.backtrace
    if fields & PAYLOAD_FIELDS["REGS"]:
        payload["registers"] = f.regs

    return payload
