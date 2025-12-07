import sys
import gdb

import tree_sitter
from tree_sitter import Language, Parser
from tree_sitter import Query, QueryCursor

import tree_sitter_c
import tree_sitter_cpp

supported_langs = {
        "c": Language(tree_sitter_c.language()),
        "c++": Language(tree_sitter_cpp.language()),
        } 


import os
import pathlib

from .enums import QUERY_FIELDS, generate_fields

FUNCTION_QUERY = b"""
    (
    function_definition
        declarator: (function_declarator
            declarator: (identifier) @func_name
        )
        body: (compound_statement) @func_body
    )
"""
VARIABLE_QUERY = b"""
    (
    declaration
        type: (_) @type
        declarator: [
        (init_declarator
            declarator: (identifier) @var_name
            value: (_) @var_value
        )
        (init_declarator
            declarator: (identifier) @var_name
        )
        (identifier) @var_name
        ]
    )
"""

class treesitter_matches:
    def __init__(
        self,
        frame = None,
        query_field = QUERY_FIELDS["FUNCTION"]
        ):
        query = self.craft_query(query_field) 

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
            self.src = f.read()
    
        q = Query(supported_langs[lang], query)
        tree = parser.parse(self.src)
        root = tree.root_node
        cursor = QueryCursor(q)
    
        self.matches = cursor.matches(root)


    def craft_query(self, fields):
        query = b""
        if fields & QUERY_FIELDS["VAR"]:
            query += VARIABLE_QUERY
        if fields & QUERY_FIELDS["FUNCTION"]:
            query += FUNCTION_QUERY
        return query

    def _text(self, node):
        return self.src[node.start_byte:node.end_byte].decode("utf-8", "replace")

    def search(self, name):
        caps = list(self.find_caps_by_name(name))[0]
        
        if "func_body" in caps:
            node = caps["func_body"][0]
        elif "var_value" in caps:
            node = caps["var_value"][0]
        elif "var_decl" in caps:
            node = caps["var_decl"][0]
        else:
            return ''

        return self.src[node.start_byte:node.end_byte].decode("utf-8", "replace")




    def find_caps_by_name(self, name):
        if isinstance(name, str):
            name = name.encode("utf-8")

        for _, caps in self.matches:
            for attr in ("var_name", "func_name"):
                if attr not in caps:
                    continue

                node = caps[attr][0]
                name_node = self.src[node.start_byte:node.end_byte]

                if name_node == name:
                    yield caps
