PYDANTIC_IMPORTS = [
    "abc",
    "collections",
    "collections.abc",
    "colorsys",
    "configparser",
    "contextlib",
    "copy",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "fractions",
    "functools",
    "ipaddress",
    "itertools",
    "json",
    "math",
    "os",
    "pathlib",
    "pickle",
    "re",
    "sys",
    "types",
    "typing",
    "typing_extensions",
    "uuid",
    "warnings",
    "weakref",
]


def check(cmd, mf):
    m = mf.findNode("pydantic")
    if m is None or m.filename is None:
        return None

    # Pydantic Cython and therefore hides imports from the
    # modulegraph machinery
    return {"packages": ["pydantic"], "includes": PYDANTIC_IMPORTS}
