#
# Recipe to copy Tcl/Tk support libraries when Python is linked
# with a regular unix install instead of a framework install.
#
import os
import sys
import textwrap

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

# New enough Tk version to skip using the oldsdk
# binaries.
NEW_TK = (8, 6, 11)


def tk_version():
    # Returns tk version as a tuple, including micro version
    import _tkinter

    tk = _tkinter.create()
    version_string = tk.call("info", "patchlevel")
    return tuple(int(x) for x in version_string.split("."))


def check(cmd, mf):
    m = mf.findNode("_tkinter")
    if m is None:
        return None

    try:
        import _tkinter  # noqa: F401
    except ImportError:
        return None

    prefix = sys.prefix if not hasattr(sys, "real_prefix") else sys.real_prefix

    paths = []
    lib = os.path.join(prefix, "lib")
    for fn in os.listdir(lib):
        if not os.path.isdir(os.path.join(lib, fn)):
            continue

        if fn.startswith("tk"):
            tk_path = fn
            paths.append(os.path.join(lib, fn))

        elif fn.startswith("tcl"):
            tcl_path = fn
            paths.append(os.path.join(lib, fn))

    if not paths:
        if tk_version() < NEW_TK:
            return {"use_old_sdk": True}
        return None

    prescript = (
        textwrap.dedent(
            """\
        def _boot_tkinter():
            import os

            resourcepath = os.environ["RESOURCEPATH"]
            os.putenv("TCL_LIBRARY", os.path.join(resourcepath, "lib/%(tcl_path)s"))
            os.putenv("TK_LIBRARY", os.path.join(resourcepath, "lib/%(tk_path)s"))
        _boot_tkinter()
        """
        )
        % {"tcl_path": tcl_path, "tk_path": tk_path}
    )

    return {
        "resources": [("lib", paths)],
        "prescripts": [StringIO(prescript)],
        "use_old_sdk": tk_version() < NEW_TK,
    }
