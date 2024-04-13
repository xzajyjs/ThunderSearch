from __future__ import absolute_import

import glob
import os

import pkg_resources


def check(cmd, mf):
    name = "PySide2"
    m = mf.findNode(name)
    if m is None or m.filename is None:
        return None

    try:
        from PySide2 import QtCore
    except ImportError:
        print("WARNING: macholib found PySide2, but cannot import")
        return {}

    plugin_dir = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)

    resources = [pkg_resources.resource_filename("py2app", "recipes/qt.conf")]
    for item in cmd.qt_plugins:
        if "/" not in item:
            item = item + "/*"

        if "*" in item:
            for path in glob.glob(os.path.join(plugin_dir, item)):
                rel_path = path[len(plugin_dir) :]  # noqa: E203
                resources.append((os.path.dirname("qt_plugins" + rel_path), [path]))
        else:
            resources.append(
                (
                    os.path.dirname(os.path.join("qt_plugins", item)),
                    [os.path.join(plugin_dir, item)],
                )
            )

    # PySide dumps some of its shared files
    # into /usr/lib, which is a system location
    # and those files are therefore not included
    # into the app bundle by default.
    from macholib.util import NOT_SYSTEM_FILES

    for fn in os.listdir("/usr/lib"):
        add = False
        if fn.startswith("libpyside2-python"):
            add = True
        elif fn.startswith("libshiboken2-python"):
            add = True
        if add:
            NOT_SYSTEM_FILES.append(os.path.join("/usr/lib", fn))

    mf.import_hook("PySide2.support", m, ["*"])
    mf.import_hook("PySide2.support.signature", m, ["*"])
    mf.import_hook("PySide2.support.signature.lib", m, ["*"])
    mf.import_hook("PySide2.support.signature.typing", m, ["*"])

    return {"resources": resources}
