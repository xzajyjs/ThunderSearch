import os

from modulegraph.modulegraph import MissingModule


def check(cmd, mf):
    m = mf.findNode("PyQt6")
    if m and not isinstance(m, MissingModule):
        try:
            # PyQt6 with sipconfig module, handled
            # by sip recipe
            import sipconfig  # noqa: F401

            return None

        except ImportError:
            pass

        try:
            import PyQt6
            from PyQt6.QtCore import QLibraryInfo
        except ImportError:
            # Dependency in the graph, but PyQt6 isn't
            # installed.
            return None

        qtdir = QLibraryInfo.path(QLibraryInfo.LibraryPath.LibrariesPath)
        if os.path.relpath(qtdir, os.path.dirname(PyQt6.__file__)).startswith("../"):
            # Qt6's prefix is not the PyQt6 package, which means
            # the "packages" directive below won't include everything
            # needed, and in particular won't include the plugins
            # folder.
            print("System install of Qt6")

            # Ensure that the Qt plugins are copied into the "Contents/plugins" folder,
            # that's where the bundles Qt expects them to be
            extra = {
                "resources": [
                    ("..", [QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)])
                ]
            }

        else:
            extra = {}

        # All imports are done from C code, hence not visible
        # for modulegraph
        # 1. Use of 'sip'
        # 2. Use of other modules, datafiles and C libraries
        #    in the PyQt5 package.
        try:
            mf.import_hook("sip", m)
        except ImportError:
            mf.import_hook("sip", m, level=1)

        result = {"packages": ["PyQt6"]}
        result.update(extra)
        return result

    return None
