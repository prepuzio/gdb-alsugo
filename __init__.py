#!/usr/bin/env python3
import gdb
import sys

# use ext libraries, not needed for now
#sys.path.append("./deps/lib/python3.13/site-packages") # not needed for now
from .cmds import cmds 

class Sugo(gdb.Command):
    def __init__(self):
        super(Sugo, self).__init__(
            "sugo",
            gdb.COMMAND_USER,
        )

        self.cmds = cmds

    def invoke(self, arg, from_tty):
        # arg is a raw string: "bp 0x401000"
        argv = gdb.string_to_argv(arg)

        if not argv:
            command = self.cmds.settings["default_command"].split()
            self.cmds[command[0]](command[1:], from_tty)

            return

        sub = argv[0]
        rest = argv[1:]


        try:
            self.cmds[sub](rest, from_tty)
        # FIXME use another error instead (keyerror  mixings)
        except KeyError as e:
            raise gdb.GdbError(f"command not found: {e}")
        except Exception as e:
            raise gdb.GdbError(f"command execution failed: {e}")

    def complete(self, text, word):
        return self.cmds.completions

Sugo()
