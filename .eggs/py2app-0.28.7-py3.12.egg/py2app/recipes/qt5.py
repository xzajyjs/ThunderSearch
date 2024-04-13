import os
import sys

from modulegraph.modulegraph import MissingModule


def check(cmd, mf):
    m = mf.findNode("PyQt5")
    if m and not isinstance(m, MissingModule):
        try:
            # PyQt5 with sipconfig module, handled
            # by sip recipe
            import sipconfig  # noqa: F401

            return None

        except ImportError:
            pass

        try:
            import PyQt5
            from PyQt5.QtCore import QLibraryInfo
        except ImportError:
            # PyQt5 in the graph, but not instaled
            return None

        # All imports are done from C code, hence not visible
        # for modulegraph
        # 1. Use of 'sip'
        # 2. Use of other modules, datafiles and C libraries
        #    in the PyQt5 package.
        try:
            mf.import_hook("PyQt5.sip", m)
        except ImportError:
            mf.import_hook("sip", m, level=1)

        qtdir = QLibraryInfo.location(QLibraryInfo.LibrariesPath)
        if os.path.relpath(qtdir, os.path.dirname(PyQt5.__file__)).startswith("../"):
            # Qt5's prefix is not the PyQt5 package, which means
            # the "packages" directive below won't include everything
            # needed, and in particular won't include the plugins
            # folder.
            print("System install of Qt5")

            # Ensure that the Qt plugins are copied into the "Contents/plugins"
            # folder, that's where the bundles Qt expects them to be
            extra = {
                "resources": [("..", [QLibraryInfo.location(QLibraryInfo.PluginsPath)])]
            }

        else:
            extra = {}

        if sys.version[0] != 2:
            result = {
                "packages": ["PyQt5"],
                "expected_missing_imports": {"copy_reg", "cStringIO", "StringIO"},
            }
            result.update(extra)
            return result
        else:
            result = {"packages": ["PyQt5"]}
            result.update(extra)
            return result

    return None
