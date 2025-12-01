#!/usr/bin/env python3
import gdb
import sys, os

_here = os.path.dirname(__file__)
_deps = os.path.join(_here, "deps")

if _deps not in sys.path:
    sys.path.insert(0, _deps)

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
            # TODO create help command
            command = 'version'
            self.cmds[command]([], from_tty)

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
        return self.cmds.keys

Sugo()
