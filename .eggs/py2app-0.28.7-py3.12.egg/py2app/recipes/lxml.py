#
# LXML uses imports from C code (or actually Cython code)
# and those cannot be detected by modulegraph.
# The check function adds the hidden imports to the graph
#
# The dependency list was extracted from lxml 3.0.2
import sys


def check(cmd, mf):
    m = mf.findNode("lxml.etree")
    if m is not None and m.filename is not None:
        mf.import_hook("lxml._elementpath", m)
        mf.import_hook("os.path", m)
        mf.import_hook("re", m)
        mf.import_hook("gzip", m)

        if sys.version_info[0] == 2:
            mf.import_hook("StringIO", m)
        else:
            mf.import_hook("io", m)

    m = mf.findNode("lxml.objectify")
    if m is not None and m.filename is not None:
        if sys.version_info[0] == 2:
            mf.import_hook("copy_reg", m)
        else:
            mf.import_hook("copyreg", m)

    m = mf.findNode("lxml.isoschematron")
    if m is not None and m.filename is not None:
        # Not zip-safe (see issue 118)
        return {"packages": ["lxml"]}

    if mf.findNode("lxml") is None:
        return None

    return {}
