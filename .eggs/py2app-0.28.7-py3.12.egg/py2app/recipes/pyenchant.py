"""
Recipe for pyEnchant <http://pypi.python.org/pypi/pyenchant>

PyEnchant is a python library that wraps a C library
using ctypes, hence the usual way to find the library
won't work.
"""
import os


def check(cmd, mf):
    m = mf.findNode("enchant")
    if m is None or m.filename is None:
        return None

    if "PYENCHANT_LIBRARY_PATH" in os.environ:
        # libpath = os.environ['PYENCHANT_LIBRARY_PATH']
        print("WARNING: using pyEnchant without embedding")
        print("WARNING: this is not supported at the moment")

    else:
        path = os.path.dirname(m.filename)
        if not os.path.exists(os.path.join(path, "lib", "libenchant.1.dylib")):
            print("WARNING: using pyEnchant without embedding")
            print("WARNING: this is not supported at the moment")

    # Include the entire package outside of site-packages.zip,
    # mostly to avoid trying to extract the C code from the package
    return {"packages": ["enchant"]}
