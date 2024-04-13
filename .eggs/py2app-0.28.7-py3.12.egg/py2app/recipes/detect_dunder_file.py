import dis
import os
import sys

from modulegraph import modulegraph

from py2app.filters import not_stdlib_filter


def get_toplevel_package_name(node):
    if isinstance(node, modulegraph.Package):
        return node.identifier.split(".")[0]
    elif isinstance(node, modulegraph.BaseModule):
        name = node.identifier
        if "." in name:
            return name.split(".")[0]

    return None


def scan_bytecode_loads(names, co):
    constants = co.co_consts
    for inst in dis.get_instructions(co):
        if inst.opname == "LOAD_NAME":
            name = co.co_names[inst.arg]
            names.add(name)

        elif inst.opname == "LOAD_GLOBAL":
            if sys.version_info[:2] >= (3, 11):
                name = co.co_names[inst.arg >> 1]
            else:
                name = co.co_names[inst.arg]
            names.add(name)

    cotype = type(co)
    for c in constants:
        if isinstance(c, cotype):
            scan_bytecode_loads(names, c)


if sys.version_info[:2] >= (3, 4):
    # Only activate this recipe for Python 3.4 or later because
    # scan_bytecode_loads doesn't work on older versions.

    def check(cmd, mf):
        packages = set()
        for node in mf.flatten():
            if not not_stdlib_filter(node):
                continue

            if node.code is None:
                continue

            if node.identifier.startswith(
                os.path.dirname(os.path.dirname(__file__)) + "/"
            ):
                continue

            if not hasattr(node, "_py2app_global_reads"):
                names = set()
                scan_bytecode_loads(names, node.code)
                node._py2app_global_reads = names

            if "__file__" in node._py2app_global_reads:
                pkg = get_toplevel_package_name(node)
                if pkg is not None:
                    packages.add(pkg)

        if packages:
            return {"packages": packages}
        return None
