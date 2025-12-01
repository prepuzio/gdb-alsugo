import sys
import gdb

# # RELATIVE PATH this is relative
sys.path.append("./deps/lib/python3.13/site-packages")
import tree_sitter
from tree_sitter import Language, Parser
import tree_sitter_c
from tree_sitter import Query, QueryCursor

supported_langs = {
        "c": Language(tree_sitter_c.language())
        } 

import os
import pathlib

FUNCTION_DEF = b"""
    (
    function_definition
        declarator: (function_declarator
            declarator: (identifier) @func_name
        )
        body: (compound_statement) @func_body
    )
    """


def treesitter_matches(
        frame = None,
        query = FUNCTION_DEF
        ):
    if frame == None:
        frame = gdb.selected_frame()
    file = frame.find_sal().symtab.fullname()
    lang = frame.language()
    try:
        parser = Parser(supported_langs[lang])
    except:
        print("unsupported language")
        return

    with open(file, "rb") as f:
        src = f.read()

    q = Query(langs[lang], query)
    tree = parser.parse(src)
    root = tree.root_node
    cursor = QueryCursor(q)

    return cursor.matches(root)

# should take frame as arg or smtg
def treesitter_get_function(name):
    frame = gdb.selected_frame()
    file = frame.find_sal().symtab.fullname()
    lang = frame.language()

    try:
        parser = Parser(supported_langs[lang])
    except:
        print("unsupported language")
        return

    with open(file, "rb") as f:
        src = f.read()

    q = Query(supported_langs[lang], b"""
    (
    function_definition
        declarator: (function_declarator
            declarator: (identifier) @func_name
        )
        body: (compound_statement) @func_body
    )
    """)
    tree = parser.parse(src)
    root = tree.root_node
    cursor = QueryCursor(q)

    for _, caps in cursor.matches(root):
        name_node = caps["func_name"][0]
        body_node = caps["func_body"][0]

        func_name = src[name_node.start_byte:name_node.end_byte].decode("utf-8", "replace")

        if func_name != name:
            continue

        # return body of the function
        return src[body_node.start_byte:body_node.end_byte].decode("utf-8", "replace")

    return None
