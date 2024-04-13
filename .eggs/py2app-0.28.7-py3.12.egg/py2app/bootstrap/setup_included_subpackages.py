import sys


def _included_subpackages(packages):
    for _pkg in packages:
        pass


class Finder(object):
    def find_spec(self, fullname, path, target=None):
        if fullname in _path_hooks: # noqa: F821
            from importlib.machinery import ModuleSpec, SourcelessFileLoader, SourceFileLoader
            from importlib.util import spec_from_loader
            import os
            pkg_dir = os.path.join(
                os.environ["RESOURCEPATH"], "lib", "python%d.%d" % (sys.version_info[:2])
            )
            init_path = os.path.join(pkg_dir, fullname, "__init__.py")
            if os.path.exists(init_path):
                loader = SourceFileLoader(fullname, init_path)
            else:
                loader = SourcelessFileLoader(fullname, init_path + "c")

            return spec_from_loader(fullname, loader)


    def find_module(self, fullname, path=None):
        if fullname in _path_hooks:  # noqa: F821
            return Loader()


class Loader(object):
    def load_module(self, fullname):
        import imp
        import os

        pkg_dir = os.path.join(
            os.environ["RESOURCEPATH"], "lib", "python%d.%d" % (sys.version_info[:2])
        )
        return imp.load_module(
            fullname, None, os.path.join(pkg_dir, fullname), ("", "", imp.PKG_DIRECTORY)
        )


sys.meta_path.insert(0, Finder())
