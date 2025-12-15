def generate_fields(names):
    yield "NONE", 0
    for i, name in enumerate(names):
        yield name, 1 << i
    yield "ALL", (1 << len(names)) - 1

# treesitter query type
QUERY_FIELDS = dict(generate_fields([
    "VAR", 
    "FUNCTION",
    "CLASS"]))

# payload generation fields
PAYLOAD_FIELDS = dict(generate_fields([
    "LINE", 
    "BODY", 
    "LIST", 
    "FUNCTION", 
    "LOCALS",
    "FILE",
    "BACKTRACE",
    "REGS"]))
