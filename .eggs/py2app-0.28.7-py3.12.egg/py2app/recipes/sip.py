"""
Py2app support for project using sip, which basicly means PyQt and wrappers
for other Qt-based libraries.

This will include all C modules that might be used when you import a package
using sip because we have no way to fine-tune this.

The problem with SIP is that all inter-module depedencies (for example from
PyQt4.Qt to PyQt4.QtCore) are handled in C code and therefore cannot be
detected by the python code in py2app).
"""
from __future__ import absolute_import

import glob
import os
import sys

import pkg_resources


class Sip(object):
    def __init__(self):
        self.packages = None
        self.plugin_dir = None

    def config(self):
        if self.packages is not None:
            print("packages", self.packages)
            return self.packages

        import os

        import sipconfig

        try:
            from PyQt4 import pyqtconfig

            cfg = pyqtconfig.Configuration()
            qtdir = cfg.qt_lib_dir
            sipdir = os.path.dirname(cfg.pyqt_mod_dir)
            self.plugin_dir = os.path.join(cfg.qt_dir, "plugins")
        except ImportError:
            from PyQt5.QtCore import QLibraryInfo

            qtdir = QLibraryInfo.location(QLibraryInfo.LibrariesPath)
            self.plugin_dir = QLibraryInfo.location(QLibraryInfo.PluginsPath)
            sipdir = os.path.dirname(sipconfig.__file__)

        if not os.path.exists(qtdir):
            print("sip: Qtdir %r does not exist" % (qtdir))
            # half-broken installation? ignore.
            raise ImportError

        # Qt is GHETTO!
        # This looks wrong, setting DYLD_LIBRARY_PATH should not be needed!
        dyld_library_path = os.environ.get("DYLD_LIBRARY_PATH", "").split(":")

        if qtdir not in dyld_library_path:
            dyld_library_path.insert(0, qtdir)
            os.environ["DYLD_LIBRARY_PATH"] = ":".join(dyld_library_path)

        self.packages = set()

        for fn in os.listdir(sipdir):
            fullpath = os.path.join(sipdir, fn)
            if os.path.isdir(fullpath):
                self.packages.add(fn)
                if fn in ("PyQt4", "PyQt5"):
                    # PyQt4 and later has a nested structure, also import
                    # subpackage to ensure everything get seen.
                    for sub in os.listdir(fullpath):
                        if ".py" not in sub:
                            self.packages.add("%s.%s" % (fn, sub.replace(".so", "")))

        print("sip: packages: %s" % (self.packages,))

        return self.packages

    def check(self, cmd, mf):
        try:
            packages = self.config()
        except ImportError:
            return None

        if "PyQt4.uic" in packages:
            # PyQt4.uic contains subpackages with python 2 and python 3
            # support. Exclude the variant that won't be ussed, this avoids
            # compilation errors on Python 2 (because some of the Python 3
            # code is not valid Python 2 code)
            if sys.version_info[0] == 2:
                ref = "PyQt4.uic.port_v3"
            else:
                ref = "PyQt4.uic.port_v2"

        if "PyQt5.uic" in packages:
            # ditto
            if sys.version_info[0] == 2:
                ref = "PyQt5.uic.port_v3"
            else:
                ref = "PyQt5.uic.port_v2"

            # Exclude...
            mf.lazynodes[ref] = None

        for pkg in packages:
            m = mf.findNode(pkg)
            if m is not None and m.filename is not None:
                break

        else:
            print("sip: No sip package used in application")
            return None

        mf.import_hook("sip", m)
        m = mf.findNode("sip")
        # naive inclusion of ALL sip packages
        # stupid C modules.. hate hate hate
        for pkg in packages:
            try:
                mf.import_hook(pkg, m)
            except ImportError as exc:
                print("WARNING: ImportError in sip recipe ignored: %s" % (exc,))

        if mf.findNode("PyQt4") is not None or mf.findNode("PyQt5") is not None:
            resources = [pkg_resources.resource_filename("py2app", "recipes/qt.conf")]

            for item in cmd.qt_plugins:
                if "/" not in item:
                    item = item + "/*"

                if "*" in item:
                    for path in glob.glob(os.path.join(self.plugin_dir, item)):
                        rel_path = path[len(self.plugin_dir) :]  # noqa: E203
                        resources.append(
                            (os.path.dirname("qt_plugins" + rel_path), [path])
                        )
                else:
                    resources.append(
                        (
                            os.path.dirname(os.path.join("qt_plugins", item)),
                            [os.path.join(self.plugin_dir, item)],
                        )
                    )

            return {"resources": resources}

        return {}


check = Sip().check
