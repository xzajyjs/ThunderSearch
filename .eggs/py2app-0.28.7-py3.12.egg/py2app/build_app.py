"""
Mac OS X .app build command for distutils

Originally (loosely) based on code from py2exe's build_exe.py by Thomas Heller.
"""
from __future__ import print_function

import collections
try:
    import imp
except ImportError:
    from modulegraph import _imp as imp
import os
import plistlib
import shlex
import shutil
import sys
import types
import zipfile
from distutils import log
from distutils.errors import DistutilsOptionError, DistutilsPlatformError
from distutils.sysconfig import get_config_h_filename, get_config_var
from distutils.util import convert_path, get_platform
from itertools import chain

import macholib.dyld
import macholib.MachO
import macholib.MachOStandalone
import pkg_resources
from macholib.util import flipwritable
from modulegraph import modulegraph, zipio
from modulegraph.find_modules import find_modules, find_needed_modules, parse_mf_results
from modulegraph.modulegraph import Package, Script, SourceModule
from modulegraph.util import imp_find_module
from setuptools import Command

from py2app import recipes
from py2app._pkg_meta import IGNORED_DISTINFO, scan_for_metadata
from py2app.apptemplate.setup import main as script_executable
from py2app.create_appbundle import create_appbundle
from py2app.create_pluginbundle import create_pluginbundle
from py2app.filters import has_filename_filter, not_stdlib_filter
from py2app.util import (
    byte_compile,
    codesign_adhoc,
    copy_file,
    copy_resource,
    copy_tree,
    fancy_split,
    find_version,
    fsencoding,
    in_system_path,
    iter_platform_files,
    make_exec,
    make_loader,
    make_symlink,
    makedirs,
    mapc,
    mergecopy,
    momc,
    skipscm,
    strip_files,
)

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


PYTHONFRAMEWORK = get_config_var("PYTHONFRAMEWORK")


PLUGIN_SUFFIXES = {
    ".qlgenerator": "QuickLook",
    ".mdimporter": "Spotlight",
    ".xpc": "XPCServices",
    ".service": "Services",
    ".prefPane": "PreferencePanes",
    ".iaplugin": "InternetAccounts",
    ".action": "Automator",
}

try:
    basestring
except NameError:
    basestring = str

if hasattr(sys, "real_prefix"):
    sys_base_prefix = sys.real_prefix
elif hasattr(sys, "base_prefix"):
    sys_base_prefix = sys.base_prefix
else:
    sys_base_prefix = sys.prefix


def finalize_distribution_options(dist):
    """
    setuptools.finalize_distribution_options extension
    point for py2app, to deail with autodiscovery in
    setuptools 61.

    This addin will set the name and py_modules attributes
    when a py2app distribution is detected that does not
    yet have these attributes.
    are not already set
    """
    if getattr(dist, "app", None) is None and getattr(dist, "plugin", None) is None:
        return

    if getattr(dist.metadata, "py_modules", None) is None:
        dist.py_modules = []

    name = getattr(dist.metadata, "name", None)
    if name is None or name == "UNKNOWN":
        if dist.app:
            targets = FixupTargets(dist.app, "script")
        else:
            targets = FixupTargets(dist.plugin, "script")

        if not targets:
            return

        base = targets[0].get_dest_base()
        name = os.path.basename(base)

        dist.metadata.name = name


def loader_paths(sourcefn, destfn):
    # Yield (sourcefn, destfn) pairs for all
    # '@loader_path' load commands in 'sourcefn'
    sourcedir = os.path.dirname(sourcefn)
    destdir = os.path.dirname(destfn)

    m = macholib.MachO.MachO(sourcefn)
    for header in m.headers:
        for _idx, _name, other in header.walkRelocatables():
            if not other.startswith("@loader_path/"):
                continue
            relpath = other[13:]
            yield os.path.join(sourcedir, relpath), os.path.join(destdir, relpath)


def rewrite_tkinter_load_commands(tkinter_path):
    m = macholib.MachO.MachO(tkinter_path)
    tcl_path = None
    tk_path = None

    rewrite_map = {}

    for header in m.headers:
        for _idx, _name, other in header.walkRelocatables():
            if other.endswith("/Tk"):
                if tk_path is not None and other != tk_path:
                    raise DistutilsPlatformError(
                        "_tkinter is linked to different Tk paths"
                    )
                tk_path = other
            elif other.endswith("/Tcl"):
                if tcl_path is not None and other != tcl_path:
                    raise DistutilsPlatformError(
                        "_tkinter is linked to different Tcl paths"
                    )
                tcl_path = other

    if tcl_path is None or "Tcl.framework" not in tcl_path:
        raise DistutilsPlatformError("_tkinter is not linked a Tcl.framework")

    if tk_path is None or "Tk.framework" not in tk_path:
        raise DistutilsPlatformError("_tkinter is not linked a Tk.framework")

    system_tcl_versions = [
        nm
        for nm in os.listdir("/System/Library/Frameworks/Tcl.framework/Versions")
        if nm != "Current"
    ]
    system_tk_versions = [
        nm
        for nm in os.listdir("/System/Library/Frameworks/Tk.framework/Versions")
        if nm != "Current"
    ]

    if not tcl_path.startswith("/System/Library/Frameworks"):
        # ../Versions/8.5/Tcl
        ver = os.path.basename(os.path.dirname(tcl_path))
        if ver not in system_tcl_versions:
            raise DistutilsPlatformError(
                "_tkinter is linked to a version of Tcl not in /System"
            )

        rewrite_map[
            tcl_path
        ] = "/System/Library/Frameworks/Tcl.framework/Versions/%s/Tcl" % (ver,)

    if not tk_path.startswith("/System/Library/Frameworks"):
        # ../Versions/8.5/Tk
        ver = os.path.basename(os.path.dirname(tk_path))
        if ver not in system_tk_versions:
            raise DistutilsPlatformError(
                "_tkinter is linked to a version of Tk not in /System"
            )

        rewrite_map[
            tk_path
        ] = "/System/Library/Frameworks/Tk.framework/Versions/%s/Tk" % (ver,)

    if rewrite_map:
        print("Relinking _tkinter.so to system Tcl/Tk")
        rewroteAny = False
        for header in m.headers:
            for idx, _name, other in header.walkRelocatables():
                data = rewrite_map.get(other)
                if data:
                    if header.rewriteDataForCommand(
                        idx, data.encode(sys.getfilesystemencoding())
                    ):
                        rewroteAny = True

        if rewroteAny:
            old_mode = flipwritable(m.filename)
            try:
                with open(m.filename, "rb+") as f:
                    for header in m.headers:
                        f.seek(0)
                        header.write(f)
                        f.seek(0, 2)
                        f.flush()

            finally:
                flipwritable(m.filename, old_mode)

    else:
        print("_tkinter already linked against system Tcl/Tk")


def get_zipfile(dist, semi_standalone=False):
    if sys.version_info[0] == 3:
        if semi_standalone:
            return "python%d.%d/site-packages.zip" % (sys.version_info[:2])
        else:
            return "python%d%d.zip" % (sys.version_info[:2])

    return getattr(dist, "zipfile", None) or "site-packages.zip"


def framework_copy_condition(src):
    # Skip Headers, .svn, and CVS dirs
    return skipscm(src) and os.path.basename(src) != "Headers"


class PythonStandalone(macholib.MachOStandalone.MachOStandalone):
    def __init__(self, appbuilder, ext_dir, copyexts, *args, **kwargs):
        super(PythonStandalone, self).__init__(*args, **kwargs)
        self.appbuilder = appbuilder
        self.ext_map = {}
        for e in copyexts:
            fn = os.path.join(
                ext_dir,
                (e.identifier.replace(".", os.sep) + os.path.splitext(e.filename)[1]),
            )
            self.ext_map[fn] = os.path.dirname(e.filename)

    def update_node(self, m):
        if isinstance(m, macholib.MachO.MachO):
            if m.filename in self.ext_map:
                m.loader_path = self.ext_map[m.filename]
        return m

    def copy_dylib(self, src):
        dest = os.path.join(self.dest, os.path.basename(src))
        if os.path.islink(src):
            dest = os.path.join(self.dest, os.path.basename(os.path.realpath(src)))

            # Ensure that the orginal name also exists, avoids problems when
            # the filename is used from Python (see issue #65)
            #
            # NOTE: The if statement checks that the target link won't
            #       point to itself, needed for systems like homebrew that
            #       store symlinks in "public" locations that point to
            #       files of the same name in a per-package install location.
            link_dest = os.path.join(self.dest, os.path.basename(src))
            if os.path.basename(link_dest) != os.path.basename(dest):
                make_symlink(os.path.basename(dest), link_dest)

        else:
            dest = os.path.join(self.dest, os.path.basename(src))

        self.ext_map[dest] = os.path.dirname(src)
        return self.appbuilder.copy_dylib(src, dest)

    def copy_framework(self, info):
        destfn = self.appbuilder.copy_framework(info, self.dest)
        dest = os.path.join(self.dest, info["shortname"] + ".framework")
        self.pending.append((destfn, iter_platform_files(dest)))
        return destfn


def iterRecipes(module=recipes):
    for name in dir(module):
        if name.startswith("_"):
            continue
        check = getattr(getattr(module, name), "check", None)
        if check is not None:
            yield (name, check)


# A very loosely defined "target".  We assume either a "script" or "modules"
# attribute.  Some attributes will be target specific.
class Target(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # If modules is a simple string, assume they meant list
        m = self.__dict__.get("modules")
        if m and isinstance(m, basestring):
            self.modules = [m]

    def __repr__(self):
        return "<Target %s>" % (self.__dict__,)

    def get_dest_base(self):
        dest_base = getattr(self, "dest_base", None)
        if dest_base:
            return dest_base

        script = getattr(self, "script", None)
        if script:
            return os.path.basename(os.path.splitext(script)[0])
        modules = getattr(self, "modules", None)
        assert modules, "no script, modules or dest_base specified"
        return modules[0].split(".")[-1]

    def validate(self):
        resources = getattr(self, "resources", [])
        for r_filename in resources:
            if not os.path.isfile(r_filename):
                raise DistutilsOptionError(
                    "Resource filename '%s' does not exist" % (r_filename,)
                )


def validate_target(dist, attr, value):
    res = FixupTargets(value, "script")
    other = {"app": "plugin", "plugin": "app"}
    if res and getattr(dist, other[attr]):
        raise DistutilsOptionError("You must specify either app or plugin, not both")


def FixupTargets(targets, default_attribute):
    if not targets:
        return targets
    try:
        targets = eval(targets)
    except:  # noqa: E722,B001
        pass
    ret = []
    for target_def in targets:
        if isinstance(target_def, basestring):
            # Create a default target object, with the string as the attribute
            target = Target(**{default_attribute: target_def})
        else:
            d = getattr(target_def, "__dict__", target_def)
            if default_attribute not in d:
                raise DistutilsOptionError(
                    "This target class requires an attribute '%s'"
                    % (default_attribute,)
                )
            target = Target(**d)
        target.validate()
        ret.append(target)
    return ret


def normalize_data_file(fn):
    if isinstance(fn, basestring):
        fn = convert_path(fn)
        return ("", [fn])
    return fn


def is_system():
    prefix = sys.prefix
    if os.path.exists(os.path.join(prefix, ".Python")):
        fn = os.path.join(
            prefix, "lib", "python%d.%d" % (sys.version_info[:2]), "orig-prefix.txt"
        )
        if os.path.exists(fn):
            if sys.version_info[0] == 2:
                with open(fn, "rU") as fp:
                    prefix = fp.read().strip()
            else:
                with open(fn, "r") as fp:
                    prefix = fp.read().strip()

    return in_system_path(prefix)


def installation_info(version=None):
    if version is None:
        version = sys.version

    if is_system():
        return ".".join(version.split(".")[:2]) + " (FORCED: Using vendor Python)"
    else:
        return ".".join(version.split(".")[:2])


class py2app(Command):
    description = "create a Mac OS X application or plugin from Python scripts"
    # List of option tuples: long name, short name (None if no short
    # name), and help string.

    user_options = [
        ("app=", None, "application bundle to be built"),
        ("plugin=", None, "plugin bundle to be built"),
        (
            "optimize=",
            "O",
            'optimization level: -O1 for "python -O", '
            '-O2 for "python -OO", and -O0 to disable [default: -O0]',
        ),
        ("includes=", "i", "comma-separated list of modules to include"),
        ("packages=", "p", "comma-separated list of packages to include"),
        ("iconfile=", None, "Icon file to use"),
        ("excludes=", "e", "comma-separated list of modules to exclude"),
        (
            "dylib-excludes=",
            "E",
            "comma-separated list of frameworks or dylibs to exclude",
        ),
        ("datamodels=", None, "xcdatamodels to be compiled and copied into Resources"),
        (
            "expected-missing-imports=",
            None,
            "expected missing imports either a comma sperated list "
            "or @ followed by file containing a list of imports, one per line",
        ),
        (
            "mappingmodels=",
            None,
            "xcmappingmodels to be compiled and copied into Resources",
        ),
        (
            "resources=",
            "r",
            "comma-separated list of additional data files and folders to "
            "include (not for code!)",
        ),
        (
            "frameworks=",
            "f",
            "comma-separated list of additional frameworks and dylibs to " "include",
        ),
        ("plist=", "P", "Info.plist template file, dict, or plistlib.Plist"),
        (
            "extension=",
            None,
            "Bundle extension [default:.app for app, .plugin for plugin]",
        ),
        ("graph", "g", "output module dependency graph"),
        ("xref", "x", "output module cross-reference as html"),
        ("no-strip", None, "do not strip debug and local symbols from output"),
        # ("compressed", 'c',
        # "create a compressed zipfile"),
        (
            "no-chdir",
            "C",
            "do not change to the data directory (Contents/Resources) "
            "[forced for plugins]",
        ),
        # ("no-zip", 'Z',
        # "do not use a zip file"),
        (
            "semi-standalone",
            "s",
            "depend on an existing installation of Python " + installation_info(),
        ),
        ("alias", "A", "Use an alias to current source file (for development only!)"),
        ("argv-emulation", "a", "Use argv emulation [disabled for plugins]."),
        ("argv-inject=", None, "Inject some commands into the argv"),
        (
            "emulate-shell-environment",
            None,
            "Emulate the shell environment you get in a Terminal window",
        ),
        (
            "use-pythonpath",
            None,
            "Allow PYTHONPATH to effect the interpreter's environment",
        ),
        (
            "use-faulthandler",
            None,
            "Enable the faulthandler in the generated bundle (Python 3.3+)",
        ),
        ("verbose-interpreter", None, "Start python in verbose mode"),
        ("bdist-base=", "b", "base directory for build library (default is build)"),
        (
            "dist-dir=",
            "d",
            "directory to put final built distributions in (default is dist)",
        ),
        (
            "site-packages",
            None,
            "include the system and user site-packages into sys.path",
        ),
        (
            "strip",
            "S",
            "strip debug and local symbols from output (on by default, for "
            "compatibility)",
        ),
        (
            "prefer-ppc",
            None,
            "Force application to run translated on i386 (LSPrefersPPC=True)",
        ),
        (
            "debug-modulegraph",
            None,
            "Drop to pdb console after the module finding phase is complete",
        ),
        (
            "debug-skip-macholib",
            None,
            "skip macholib phase (app will not be standalone!)",
        ),
        (
            "arch=",
            None,
            "set of architectures to use (fat, fat3, universal, intel, "
            "i386, ppc, x86_64; default is the set for the current python "
            "binary)",
        ),
        (
            "qt-plugins=",
            None,
            "set of Qt plugins to include in the application bundle " "(default None)",
        ),
        (
            "matplotlib-backends=",
            None,
            "set of matplotlib backends to include (default: all)",
        ),
        (
            "extra-scripts=",
            None,
            "set of additonal scripts to include in the application bundle",
        ),
        ("include-plugins=", None, "List of plugins to include"),
        (
            "force-system-tk",
            None,
            "Ensure that Tkinter is linked against Apple's build of Tcl/Tk",
        ),
        (
            "report-missing-from-imports",
            None,
            "Report the list of missing names for 'from module import name'",
        ),
        (
            "no-report-missing-conditional-import",
            None,
            "Don't report missing modules from conditional imports",
        ),
        (
            "redirect-stdout-to-asl",
            None,
            "Forward the stdout/stderr streams to Console.app using ASL",
        ),
    ]

    boolean_options = [
        # "compressed",
        "xref",
        "strip",
        "no-strip",
        "site-packages",
        "semi-standalone",
        "alias",
        "argv-emulation",
        # "no-zip",
        "use-pythonpath",
        "use-faulthandler",
        "verbose-interpreter",
        "no-chdir",
        "debug-modulegraph",
        "debug-skip-macholib",
        "graph",
        "prefer-ppc",
        "emulate-shell-environment",
        "force-system-tk",
        "report-missing-from-imports",
        "no-report-missing-conditional-import",
        "redirect-stdout-to-asl",
    ]

    always_expected_missing_imports = {
        "org",
        "java",  # Jython only
        "_frozen_importlib_external",  # Seems to be side effect of py2app
    }

    def initialize_options(self):
        self.app = None
        self.plugin = None
        self.bdist_base = None
        self.xref = False
        self.graph = False
        self.no_zip = 0
        self.optimize = None
        # self.optimize = 0
        # if hasattr(sys, 'flags'):
        # self.optimize = sys.flags.optimize
        self.arch = None
        self.strip = True
        self.no_strip = False
        self.iconfile = None
        self.extension = None
        self.alias = 0
        self.argv_emulation = 0
        self.emulate_shell_environment = 0
        self.argv_inject = None
        self.no_chdir = 0
        self.site_packages = False
        self.use_pythonpath = False
        self.use_faulthandler = False
        self.verbose_interpreter = False
        self.includes = None
        self.packages = None
        self.excludes = None
        self.dylib_excludes = None
        self.frameworks = None
        self.resources = None
        self.datamodels = None
        self.mappingmodels = None
        self.plist = None
        self.compressed = True
        self.semi_standalone = is_system()
        self.dist_dir = None
        self.debug_skip_macholib = False
        self.debug_modulegraph = False
        self.prefer_ppc = False
        self.filters = []
        self.eggs = []
        self.qt_plugins = None
        self.matplotlib_backends = None
        self.extra_scripts = None
        self.include_plugins = None
        self.force_system_tk = False
        self.report_missing_from_imports = False
        self.no_report_missing_conditional_import = False
        self.redirect_stdout_to_asl = False
        self._python_app = None
        self.use_old_sdk = False
        self.expected_missing_imports = None

    def finalize_options(self):
        if self.prefer_ppc:
            print(
                "WARNING: Option --prefer-ppc is deprecated an will be removed "
                "in a future version. Use --arch instead"
            )

        if sys_base_prefix != sys.prefix:
            self._python_app = os.path.join(sys_base_prefix, "Resources", "Python.app")

        elif os.path.exists(os.path.join(sys.prefix, "pyvenv.cfg")):
            with open(os.path.join(sys.prefix, "pyvenv.cfg")) as fp:
                for line in fp:
                    if line.startswith("home = "):
                        _, home_path = line.split("=", 1)
                        prefix = os.path.dirname(home_path.strip())
                        break

                else:
                    raise DistutilsPlatformError(
                        "Pyvenv detected, but cannot determine base prefix"
                    )

                self._python_app = os.path.join(prefix, "Resources", "Python.app")

        elif os.path.exists(os.path.join(sys.prefix, ".Python")):
            fn = os.path.join(
                sys.prefix,
                "lib",
                "python%d.%d" % (sys.version_info[:2]),
                "orig-prefix.txt",
            )
            if os.path.exists(fn):
                if sys.version_info[0] == 2:
                    with open(fn, "rU") as fp:
                        prefix = fp.read().strip()
                        self._python_app = os.path.join(
                            prefix, "Resources", "Python.app"
                        )
                else:
                    with open(fn, "r") as fp:
                        prefix = fp.read().strip()
                        self._python_app = os.path.join(
                            prefix, "Resources", "Python.app"
                        )
            else:
                raise DistutilsPlatformError(
                    "Virtualenv detected, but cannot determine base prefix"
                )

        else:
            self._python_app = os.path.join(sys.prefix, "Resources", "Python.app")

        if self.optimize is None:
            self.optimize = 0
            if hasattr(sys, "flags"):
                self.optimize = sys.flags.optimize

        if not self.strip:
            self.no_strip = True
        elif self.no_strip:
            self.strip = False
        self.optimize = int(self.optimize)
        if self.argv_inject and isinstance(self.argv_inject, basestring):
            self.argv_inject = shlex.split(self.argv_inject)
        self.includes = set(fancy_split(self.includes))
        self.includes.add("encodings.*")
        self.includes.add("_sitebuiltins")

        if self.use_faulthandler:
            self.includes.add("faulthandler")
        self.packages = set(fancy_split(self.packages))

        self.excludes = set(fancy_split(self.excludes))
        self.excludes.add("readline")
        # included by apptemplate
        self.excludes.add("site")
        if getattr(self.distribution, "install_requires", None):
            self.includes.add("pkg_resources")
            self.eggs = pkg_resources.require(self.distribution.install_requires)

        # Setuptools/distribute style namespace packages uses
        # __import__('pkg_resources'), and that import isn't detected at the
        # moment. Forcefully include pkg_resources.
        self.includes.add("pkg_resources")

        dylib_excludes = fancy_split(self.dylib_excludes)
        self.dylib_excludes = []
        for fn in dylib_excludes:
            try:
                res = macholib.dyld.framework_find(fn)
            except ValueError:
                try:
                    res = macholib.dyld.dyld_find(fn)
                except ValueError:
                    res = fn
            self.dylib_excludes.append(res)
        self.resources = fancy_split(self.resources)
        frameworks = fancy_split(self.frameworks)
        self.frameworks = []
        for fn in frameworks:
            try:
                res = macholib.dyld.framework_find(fn)
            except ValueError:
                res = macholib.dyld.dyld_find(fn)
            while res in self.dylib_excludes:
                self.dylib_excludes.remove(res)
            self.frameworks.append(res)
        if not self.plist:
            self.plist = {}
        if isinstance(self.plist, basestring):

            if hasattr(plistlib, "load"):
                with open(self.plist, "rb") as fp:
                    self.plist = plistlib.load(fp)
            else:
                # 2.7
                self.plist = plistlib.Plist.fromFile(self.plist)
        if hasattr(plistlib, "Dict") and isinstance(self.plist, plistlib.Dict):
            # 2.7
            self.plist = dict(self.plist.__dict__)
        else:
            self.plist = dict(self.plist)

        self.set_undefined_options(
            "bdist", ("dist_dir", "dist_dir"), ("bdist_base", "bdist_base")
        )

        if self.semi_standalone:
            self.filters.append(not_stdlib_filter)

        if self.iconfile is None and "CFBundleIconFile" not in self.plist:
            # Default is the generic applet icon in the framework
            iconfile = os.path.join(
                self._python_app, "Contents", "Resources", "PythonApplet.icns"
            )
            if os.path.exists(iconfile):
                self.iconfile = iconfile

        self.runtime_preferences = list(self.get_runtime_preferences())

        self.qt_plugins = fancy_split(self.qt_plugins)
        self.matplotlib_backends = fancy_split(self.matplotlib_backends)
        self.extra_scripts = fancy_split(self.extra_scripts)
        self.include_plugins = fancy_split(self.include_plugins)

        if self.expected_missing_imports is None:
            self.expected_missing_imports = self.always_expected_missing_imports
        else:
            if self.expected_missing_imports.startswith("@"):
                self.expected_missing_imports = self.read_expected_missing_imports_file(
                    self.expected_missing_imports[1:]
                )
            else:
                self.expected_missing_imports = set(
                    fancy_split(self.expected_missing_imports)
                )
            self.expected_missing_imports |= self.always_expected_missing_imports

        if self.datamodels:
            print(
                "WARNING: the datamodels option is deprecated, "
                "add model files to the list of resources"
            )

        if self.mappingmodels:
            print(
                "WARNING: the mappingmodels option is deprecated, "
                "add model files to the list of resources"
            )

    def read_expected_missing_imports_file(self, filename):
        #
        #   ignore blank lines and lines that start with a '#'
        #   only one import per line
        #
        expected_missing_imports = set()
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                expected_missing_imports.add(line)

        return expected_missing_imports

    def get_default_plist(self):
        plist = {}
        target = self.targets[0]

        version = self.distribution.get_version()
        if version == "0.0.0":
            try:
                version = find_version(target.script)
            except ValueError:
                pass

        if not isinstance(version, basestring):
            raise DistutilsOptionError("Version must be a string")

        if sys.version_info[0] > 2 and isinstance(version, type("a".encode("ascii"))):
            raise DistutilsOptionError("Version must be a string")

        plist["CFBundleVersion"] = version

        name = self.distribution.get_name()
        if name == "UNKNOWN":
            base = target.get_dest_base()
            name = os.path.basename(base)
        plist["CFBundleName"] = name

        return plist

    def get_runtime(self, prefix=None, version=None):
        # this is a bit of a hack!
        # ideally we'd use dylib functions to figure this out
        if prefix is None:
            prefix = sys.prefix
        if version is None:
            version = sys.version
        version = ".".join(version.split(".")[:2])
        info = None
        if sys_base_prefix != sys.prefix:
            prefix = sys_base_prefix

        elif os.path.exists(os.path.join(prefix, "pyvenv.cfg")):
            with open(os.path.join(prefix, "pyvenv.cfg")) as fp:
                for ln in fp:
                    if ln.startswith("home = "):
                        _, home_path = ln.split("=", 1)
                        prefix = os.path.dirname(home_path.strip())
                        break
                else:
                    raise DistutilsPlatformError(
                        "Pyvenv detected, cannot determine base prefix"
                    )

        elif os.path.exists(os.path.join(prefix, ".Python")):
            # We're in a virtualenv environment, locate the real prefix
            fn = os.path.join(
                prefix, "lib", "python%d.%d" % (sys.version_info[:2]), "orig-prefix.txt"
            )

            if os.path.exists(fn):
                if sys.version_info[0] == 2:
                    with open(fn, "rU") as fp:
                        prefix = fp.read().strip()
                else:
                    with open(fn, "r") as fp:
                        prefix = fp.read().strip()

        try:
            fmwk = macholib.dyld.framework_find(prefix)
        except ValueError:
            info = None
        else:
            info = macholib.dyld.framework_info(fmwk)

        if info is not None:
            dylib = info["name"]
            runtime = os.path.join(info["location"], info["name"])
        else:
            dylib = "libpython%d.%d.dylib" % (sys.version_info[:2])
            runtime = os.path.join(prefix, "lib", dylib)

        return dylib, runtime

    def get_runtime_preferences(self, prefix=None, version=None):
        dylib, runtime = self.get_runtime(prefix=prefix, version=version)
        yield os.path.join("@executable_path", "..", "Frameworks", dylib)
        if self.semi_standalone or self.alias:
            yield runtime

    def run(self):
        if get_config_var("PYTHONFRAMEWORK") is None:
            if not get_config_var("Py_ENABLE_SHARED"):
                raise DistutilsPlatformError(
                    "This python does not have a shared library or framework"
                )

            else:
                # Issue .. in py2app's tracker, and issue .. in python's
                # tracker: a unix-style shared library build did not read the
                # application environment correctly. The collection of
                # if statements below gives a clean error message when py2app
                # is started, instead of building a bundle that will give a
                # confusing error message when started.
                msg = (
                    "py2app is not supported for a shared library build "
                    "with this version of python"
                )
                if sys.version_info[:2] < (2, 7):
                    raise DistutilsPlatformError(msg)
                elif sys.version_info[:2] == (2, 7) and sys.version_info[3] < 4:
                    raise DistutilsPlatformError(msg)
                elif sys.version_info[0] == 3 and sys.version_info[1] < 2:
                    raise DistutilsPlatformError(msg)
                elif sys.version_info[:2] == (3, 2) and sys.version_info[3] < 3:
                    raise DistutilsPlatformError(msg)
                elif sys.version_info[:2] == (3, 3) and sys.version_info[3] < 1:
                    raise DistutilsPlatformError(msg)

        if (
            hasattr(self.distribution, "install_requires")
            and self.distribution.install_requires
        ):

            self.distribution.fetch_build_eggs(self.distribution.install_requires)

        build = self.reinitialize_command("build")
        build.build_base = self.bdist_base
        build.run()
        self.create_directories()
        self.fixup_distribution()
        self.initialize_plist()

        sys_old_path = sys.path[:]
        extra_paths = [os.path.dirname(target.script) for target in self.targets]
        extra_paths.extend([build.build_platlib, build.build_lib])
        self.additional_paths = [
            os.path.abspath(p) for p in extra_paths if p is not None
        ]
        sys.path[:0] = self.additional_paths

        # this needs additional_paths
        self.initialize_prescripts()

        try:
            self._run()
        finally:
            sys.path = sys_old_path

    def iter_datamodels(self, resdir):
        for (path, files) in (
            normalize_data_file(fn) for fn in (self.datamodels or ())
        ):
            path = fsencoding(path)
            for fn in files:
                fn = fsencoding(fn)
                basefn, ext = os.path.splitext(fn)
                if ext != ".xcdatamodel":
                    basefn = fn
                    fn += ".xcdatamodel"
                destfn = os.path.basename(basefn) + ".mom"
                yield fn, os.path.join(resdir, path, destfn)

    def compile_datamodels(self, resdir):
        for src, dest in self.iter_datamodels(resdir):
            print("compile datamodel", src, "->", dest)
            self.mkpath(os.path.dirname(dest))
            momc(src, dest)

    def iter_mappingmodels(self, resdir):
        for (path, files) in (
            normalize_data_file(fn) for fn in (self.mappingmodels or ())
        ):
            path = fsencoding(path)
            for fn in files:
                fn = fsencoding(fn)
                basefn, ext = os.path.splitext(fn)
                if ext != ".xcmappingmodel":
                    basefn = fn
                    fn += ".xcmappingmodel"
                destfn = os.path.basename(basefn) + ".cdm"
                yield fn, os.path.join(resdir, path, destfn)

    def compile_mappingmodels(self, resdir):
        for src, dest in self.iter_mappingmodels(resdir):
            self.mkpath(os.path.dirname(dest))
            mapc(src, dest)

    def iter_extra_plugins(self):
        for item in self.include_plugins:
            if isinstance(item, (list, tuple)):
                subdir, path = item

            else:
                ext = os.path.splitext(item)[1]
                try:
                    subdir = PLUGIN_SUFFIXES[ext]
                    path = item
                except KeyError:
                    raise DistutilsOptionError(
                        "Cannot determine subdirectory for plugin %s" % (item,)
                    )

            yield path, os.path.join(subdir, os.path.basename(path))

    def iter_data_files(self):
        dist = self.distribution
        allres = chain(getattr(dist, "data_files", ()) or (), self.resources)
        for (path, files) in (normalize_data_file(fn) for fn in allres):
            path = fsencoding(path)
            for fn in files:
                fn = fsencoding(fn)
                yield fn, os.path.join(path, os.path.basename(fn))

    def collect_scripts(self):
        # these contains file names
        scripts = set()

        for target in self.targets:
            scripts.add(target.script)
            scripts.update([k for k in target.prescripts if isinstance(k, basestring)])
            if hasattr(target, "extra_scripts"):
                scripts.update(target.extra_scripts)

        scripts.update(self.extra_scripts)
        return scripts

    def get_plist_options(self):
        result = {
            "PyOptions": {
                "use_pythonpath": bool(self.use_pythonpath),
                "site_packages": bool(self.site_packages),
                "alias": bool(self.alias),
                "argv_emulation": bool(self.argv_emulation),
                "emulate_shell_environment": bool(self.emulate_shell_environment),
                "no_chdir": bool(self.no_chdir),
                "prefer_ppc": self.prefer_ppc,
                "verbose": self.verbose_interpreter,
                "use_faulthandler": self.use_faulthandler,
            },
        }
        if self.optimize:
            result["PyOptions"]["optimize"] = self.optimize
        return result

    def initialize_plist(self):
        plist = self.get_default_plist()
        for target in self.targets:
            plist.update(getattr(target, "plist", {}))
        plist.update(self.plist)
        plist.update(self.get_plist_options())

        if self.iconfile:
            iconfile = self.iconfile
            if not os.path.exists(iconfile):
                iconfile = iconfile + ".icns"
            if not os.path.exists(iconfile):
                raise DistutilsOptionError(
                    "icon file must exist: %r" % (self.iconfile,)
                )
            self.resources.append(iconfile)
            plist["CFBundleIconFile"] = os.path.basename(iconfile)
        if self.prefer_ppc:
            plist["LSPrefersPPC"] = True

        self.plist = plist
        return plist

    def run_alias(self):
        self.app_files = []
        for target in self.targets:

            extra_scripts = list(self.extra_scripts)
            if hasattr(target, "extra_scripts"):
                extra_scripts.update(extra_scripts)

            dst = self.build_alias_executable(target, target.script, extra_scripts)
            self.app_files.append(dst)

            for fn in extra_scripts:
                if fn.endswith(".py"):
                    fn = fn[:-3]
                elif fn.endswith(".pyw"):
                    fn = fn[:-4]

                src_fn = script_executable(
                    arch=self.arch, secondary=True, use_old_sdk=self.use_old_sdk
                )
                tgt_fn = os.path.join(
                    target.appdir, "Contents", "MacOS", os.path.basename(fn)
                )
                mergecopy(src_fn, tgt_fn)
                make_exec(tgt_fn)

            arch = self.arch if self.arch is not None else get_platform().split("-")[-1]
            if arch in ("universal2", "arm64"):
                codesign_adhoc(target.appdir)

    def collect_recipedict(self):
        return dict(iterRecipes())

    def get_modulefinder(self):
        if self.debug_modulegraph:
            debug = 4
        else:
            debug = 0
        return find_modules(
            scripts=self.collect_scripts(),
            includes=self.includes,
            packages=self.packages,
            excludes=self.excludes,
            debug=debug,
        )

    def collect_filters(self):
        return [has_filename_filter] + list(self.filters)

    def process_recipes(self, mf, filters, flatpackages, loader_files):
        rdict = self.collect_recipedict()
        while True:
            for name, check in rdict.items():
                rval = check(self, mf)
                if rval is None:
                    print("--- Skipping recipe %s ---" % (name,))
                    continue
                # we can pull this off so long as we stop the iter
                del rdict[name]
                print("*** using recipe: %s ***" % (name,), rval)

                if "expected_missing_imports" in rval:
                    self.expected_missing_imports |= rval.get(
                        "expected_missing_imports"
                    )

                if rval.get("packages"):
                    self.packages.update(rval["packages"])
                    find_needed_modules(mf, packages=rval["packages"])

                for pkg in rval.get("flatpackages", ()):
                    if isinstance(pkg, basestring):
                        pkg = (os.path.basename(pkg), pkg)
                    flatpackages[pkg[0]] = pkg[1]
                filters.extend(rval.get("filters", ()))
                loader_files.extend(rval.get("loader_files", ()))
                newbootstraps = list(
                    map(self.get_bootstrap, rval.get("prescripts", ()))
                )

                if rval.get("includes"):
                    find_needed_modules(mf, includes=rval["includes"])

                if rval.get("resources"):
                    self.resources.extend(rval["resources"])

                if rval.get("frameworks"):
                    self.frameworks.extend(rval["frameworks"])

                if rval.get("use_old_sdk"):
                    self.use_old_sdk = True

                for fn in newbootstraps:
                    if isinstance(fn, basestring):
                        mf.run_script(fn)

                for target in self.targets:
                    target.prescripts.extend(newbootstraps)
                break
            else:
                break

    def _run(self):
        try:
            if self.alias:
                self.run_alias()
            else:
                self.run_normal()
        except:  # noqa: E722,B001
            raise
            # import pdb
            # import sys
            # import traceback
            #
            # traceback.print_exc()
            # pdb.post_mortem(sys.exc_info()[2])
        #
        print("Done!")

    def filter_dependencies(self, mf, filters):
        print("*** filtering dependencies ***")
        nodes_seen, nodes_removed, nodes_orphaned = mf.filterStack(filters)
        print("%d total" % (nodes_seen,))
        print("%d filtered" % (nodes_removed,))
        print("%d orphaned" % (nodes_orphaned,))
        print("%d remaining" % (nodes_seen - nodes_removed,))

    def get_appname(self):
        return self.plist["CFBundleName"]

    def build_xref(self, mf, flatpackages):
        for target in self.targets:
            base = target.get_dest_base()
            appdir = os.path.join(self.dist_dir, os.path.dirname(base))
            appname = self.get_appname()
            dgraph = os.path.join(appdir, appname + ".html")
            print("*** creating dependency html: %s ***" % (os.path.basename(dgraph),))
            with open(dgraph, "w") as fp:
                mf.create_xref(fp)

    def build_graph(self, mf, flatpackages):
        for target in self.targets:
            base = target.get_dest_base()
            appdir = os.path.join(self.dist_dir, os.path.dirname(base))
            appname = self.get_appname()
            dgraph = os.path.join(appdir, appname + ".dot")
            print("*** creating dependency graph: %s ***" % (os.path.basename(dgraph),))
            with open(dgraph, "w") as fp:
                mf.graphreport(fp, flatpackages=flatpackages)

    def finalize_modulefinder(self, mf):
        for item in mf.flatten():
            if isinstance(item, Package) and item.filename == "-":
                # In python3.3 or later the default importer supports namespace
                # packages without an __init__ file, don't use that
                # funcionality because that causes problems with our suppport
                # for loading C extensions.
                #
                # if sys.version_info[:2] <= (3,3):
                if 1:
                    fn = os.path.join(self.temp_dir, "empty_package", "__init__.py")
                    if not os.path.exists(fn):
                        dn = os.path.dirname(fn)
                        if not os.path.exists(dn):
                            os.makedirs(dn)
                        with open(fn, "w"):
                            pass

                    item.filename = fn

        py_files, extensions = parse_mf_results(mf)

        # Remove all top-level scripts from the list of python files,
        # those get treated differently.
        py_files = [item for item in py_files if not isinstance(item, Script)]

        extensions = list(extensions)
        return py_files, extensions

    def collect_packagedirs(self):
        return list(
            filter(
                os.path.exists,
                [
                    os.path.join(os.path.realpath(self.get_bootstrap(pkg)), "")
                    for pkg in self.packages
                ],
            )
        )

    def may_log_missing(self, module_name):
        module_parts = module_name.split(".")
        for num_parts in range(1, len(module_parts) + 1):
            module_id = ".".join(module_parts[0:num_parts])
            if module_id in self.expected_missing_imports:
                return False

        return True

    def run_normal(self):
        mf = self.get_modulefinder()
        filters = self.collect_filters()
        flatpackages = {}
        loader_files = []
        self.process_recipes(mf, filters, flatpackages, loader_files)

        if self.debug_modulegraph:
            import pdb

            pdb.Pdb().set_trace()

        self.filter_dependencies(mf, filters)

        if self.graph:
            self.build_graph(mf, flatpackages)
        if self.xref:
            self.build_xref(mf, flatpackages)

        py_files, extensions = self.finalize_modulefinder(mf)
        pkgdirs = self.collect_packagedirs()
        self.create_binaries(py_files, pkgdirs, extensions, loader_files)

        missing = []
        syntax_error = []
        invalid_bytecode = []
        invalid_relative_import = []

        for module in mf.nodes():
            if isinstance(module, modulegraph.MissingModule):
                if module.identifier != "__main__":
                    missing.append(module)
            elif isinstance(module, modulegraph.InvalidSourceModule):
                syntax_error.append(module)
            elif hasattr(modulegraph, "InvalidCompiledModule") and isinstance(
                module, modulegraph.InvalidCompiledModule
            ):
                invalid_bytecode.append(module)
            elif hasattr(modulegraph, "InvalidRelativeImport") and isinstance(
                module, modulegraph.InvalidRelativeImport
            ):
                invalid_relative_import.append(module)

        if missing:
            missing_unconditional = collections.defaultdict(set)
            missing_fromimport = collections.defaultdict(set)
            missing_fromimport_conditional = collections.defaultdict(set)
            missing_conditional = collections.defaultdict(set)

            log.info("checking for any import problems")
            for module in sorted(missing):
                for m in mf.getReferers(module):
                    if m is None:
                        continue

                    try:
                        ed = mf.edgeData(m, module)
                    except KeyError:
                        ed = None

                    if hasattr(modulegraph, "DependencyInfo") and isinstance(
                        ed, modulegraph.DependencyInfo
                    ):
                        c = missing_unconditional
                        if ed.conditional or ed.function:
                            if ed.fromlist:
                                c = missing_fromimport_conditional
                            else:
                                c = missing_conditional

                        elif ed.fromlist:
                            c = missing_fromimport

                        c[module.identifier].add(m.identifier)

                    else:
                        missing_unconditional[module.identifier].add(m.identifier)

            if missing_unconditional:
                warnings = []
                for m in sorted(missing_unconditional):
                    try:
                        if "." in m:
                            m1, m2 = m.rsplit(".", 1)
                            try:
                                o = __import__(m1, fromlist=[m2])
                                o = getattr(o, m2)
                            except Exception:
                                if self.may_log_missing(m):
                                    warnings.append(
                                        " * %s (%s)"
                                        % (
                                            m,
                                            ", ".join(sorted(missing_unconditional[m])),
                                        )
                                    )
                                continue

                        else:
                            o = __import__(m)

                        if isinstance(o, types.ModuleType):
                            if self.may_log_missing(m):
                                warnings.append(
                                    " * %s (%s) [module alias]"
                                    % (m, ", ".join(sorted(missing_unconditional[m])))
                                )

                    except ImportError:
                        if self.may_log_missing(m):
                            warnings.append(
                                " * %s (%s)"
                                % (m, ", ".join(sorted(missing_unconditional[m])))
                            )

                if len(warnings) > 0:
                    log.warn("Modules not found (unconditional imports):")
                    for msg in warnings:
                        log.warn(msg)
                    log.warn("")

            if missing_conditional and not self.no_report_missing_conditional_import:
                warnings = []
                for m in sorted(missing_conditional):
                    try:
                        if "." in m:
                            m1, m2 = m.rsplit(".", 1)
                            o = __import__(m1, fromlist=[m2])
                            try:
                                o = getattr(o, m2)
                            except Exception:
                                if self.may_log_missing(m):
                                    warnings.append(
                                        " * %s (%s)"
                                        % (
                                            m,
                                            ", ".join(sorted(missing_unconditional[m])),
                                        )
                                    )
                                continue

                        else:
                            o = __import__(m)

                        if isinstance(o, types.ModuleType):
                            if self.may_log_missing(m):
                                warnings.append(
                                    " * %s (%s) [module alias]"
                                    % (m, ", ".join(sorted(missing_unconditional[m])))
                                )
                    except ImportError:
                        if self.may_log_missing(m):
                            warnings.append(
                                " * %s (%s)"
                                % (m, ", ".join(sorted(missing_conditional[m])))
                            )

                if len(warnings) > 0:
                    log.warn("Modules not found (conditional imports):")
                    for msg in warnings:
                        log.warn(msg)
                    log.warn("")

            if self.report_missing_from_imports and (
                missing_fromimport
                or (
                    not self.no_report_missing_conditional_import
                    and missing_fromimport_conditional
                )
            ):
                log.warn("Modules not found ('from ... import y'):")
                for m in sorted(missing_fromimport):
                    log.warn(
                        " * %s (%s)" % (m, ", ".join(sorted(missing_fromimport[m])))
                    )

                if (
                    not self.no_report_missing_conditional_import
                    and missing_fromimport_conditional
                ):
                    log.warn("")
                    log.warn("Conditional:")
                    for m in sorted(missing_fromimport_conditional):
                        log.warn(
                            " * %s (%s)"
                            % (m, ", ".join(sorted(missing_fromimport_conditional[m])))
                        )
                log.warn("")

        if syntax_error:
            log.warn("Modules with syntax errors:")
            for module in sorted(syntax_error):
                log.warn(" * %s" % (module.identifier))

            log.warn("")

        if invalid_relative_import:
            log.warn("Modules with invalid relative imports:")

            imports = collections.defaultdict(set)

            for module in sorted(invalid_relative_import):
                for n in mf.get_edges(module)[1]:
                    imports[n.identifier].add(module.relative_path)

            for mod in sorted(imports):
                log.warn(
                    " * %s (importing %s)" % (mod, ", ".join(sorted(imports[mod])))
                )

        if invalid_bytecode:
            log.warn("Modules with invalid bytecode:")
            for module in sorted(invalid_bytecode):
                log.warn(" * %s" % (module.identifier))

            log.warn("")

    def create_directories(self):
        bdist_base = self.bdist_base
        if self.semi_standalone:
            self.bdist_dir = os.path.join(
                bdist_base,
                "python%d.%d-semi_standalone" % (sys.version_info[:2]),
                "app",
            )
        else:
            self.bdist_dir = os.path.join(
                bdist_base, "python%d.%d-standalone" % (sys.version_info[:2]), "app"
            )

        if os.path.exists(self.bdist_dir):
            shutil.rmtree(self.bdist_dir)

        self.collect_dir = os.path.abspath(os.path.join(self.bdist_dir, "collect"))
        self.mkpath(self.collect_dir)

        self.temp_dir = os.path.abspath(os.path.join(self.bdist_dir, "temp"))
        self.mkpath(self.temp_dir)

        self.dist_dir = os.path.abspath(self.dist_dir)
        self.mkpath(self.dist_dir)

        self.lib_dir = os.path.join(
            self.bdist_dir,
            os.path.dirname(get_zipfile(self.distribution, self.semi_standalone)),
        )
        self.mkpath(self.lib_dir)

        self.ext_dir = os.path.join(self.lib_dir, "lib-dynload")
        self.mkpath(self.ext_dir)

        self.framework_dir = os.path.join(self.bdist_dir, "Frameworks")
        self.mkpath(self.framework_dir)

    def create_binaries(self, py_files, pkgdirs, extensions, loader_files):
        print("*** create binaries ***")
        dist = self.distribution
        pkgexts = []
        copyexts = []
        extmap = {}
        included_metadata = set()

        metadata_infos = scan_for_metadata(sys.path)

        def packagefilter(mod, pkgdirs=pkgdirs):
            fn = os.path.realpath(getattr(mod, "filename", None))
            if fn is None:
                return None
            for pkgdir in pkgdirs:
                if fn.startswith(pkgdir):
                    return None
            return fn

        for mod in py_files + extensions:
            fn = os.path.realpath(getattr(mod, "filename", None))
            if fn is None:
                return None

            dist_info_path = metadata_infos.get(fn, None)
            if dist_info_path is None and (fn.endswith(".pyc") or fn.endswith(".pyo")):
                dist_info_path = metadata_infos.get(fn[:-1], None)
            if dist_info_path is not None:
                print("ADD INFO", dist_info_path)
                included_metadata.add(dist_info_path)

        def files_in_dir(toplevel):
            for dirname, _, fns in os.walk(toplevel):
                for fn in fns:
                    yield os.path.realpath(os.path.join(dirname, fn))

        for pd in pkgdirs:
            # Ensure that packages included through the packages option
            # get their metadata included as well, even if the python
            # package contains files from multiple package distributions
            for fn in files_in_dir(pd):
                dist_info_path = metadata_infos.get(fn, None)
                if dist_info_path is None and (
                    fn.endswith(".pyc") or fn.endswith(".pyo")
                ):
                    dist_info_path = metadata_infos.get(fn[:-1], None)
                if dist_info_path is not None:
                    included_metadata.add(dist_info_path)

        if pkgdirs:
            py_files = list(filter(packagefilter, py_files))
        for ext in extensions:
            fn = packagefilter(ext)
            if fn is None:
                fn = os.path.realpath(getattr(ext, "filename", None))
                pkgexts.append(ext)
            else:
                if "." in ext.identifier:
                    py_files.append(self.create_loader(ext))
                copyexts.append(ext)
            extmap[fn] = ext

        # byte compile the python modules into the target directory
        print("*** byte compile python files ***")
        byte_compile(
            py_files,
            target_dir=self.collect_dir,
            optimize=self.optimize,
            force=self.force,
            verbose=self.verbose,
            dry_run=self.dry_run,
        )

        for item in py_files:
            if not isinstance(item, Package):
                continue
            self.copy_package_data(item, self.collect_dir)

        # copy package metadata
        for pkg_info_path in included_metadata:
            base = os.path.join(self.collect_dir, os.path.basename(pkg_info_path))
            os.mkdir(base)

            for fn in os.listdir(pkg_info_path):
                if fn in IGNORED_DISTINFO:
                    continue
                src = os.path.join(pkg_info_path, fn)
                dst = os.path.join(base, fn)

                if os.path.isdir(src):
                    self.copy_tree(src, dst, preserve_symlinks=False)
                else:
                    self.copy_file(src, dst)
        self.lib_files = []
        self.app_files = []

        # create the shared zipfile containing all Python modules
        archive_name = os.path.join(
            self.lib_dir, get_zipfile(dist, self.semi_standalone)
        )

        for path, files in loader_files:
            dest = os.path.join(self.collect_dir, path)
            self.mkpath(dest)
            for fn in files:
                destfn = os.path.join(dest, os.path.basename(fn))
                if os.path.isdir(fn):
                    self.copy_tree(fn, destfn, preserve_symlinks=False)
                else:
                    self.copy_file(fn, destfn)

        arcname = self.make_lib_archive(
            archive_name,
            base_dir=self.collect_dir,
            verbose=self.verbose,
            dry_run=self.dry_run,
        )

        # build the executables
        for target in self.targets:
            extra_scripts = list(self.extra_scripts)
            if hasattr(target, "extra_scripts"):
                extra_scripts.extend(target.extra_scripts)

            dst = self.build_executable(
                target, arcname, pkgexts, copyexts, target.script, extra_scripts
            )
            exp = os.path.join(dst, "Contents", "MacOS")
            execdst = os.path.join(exp, "python")
            if self.semi_standalone:
                make_symlink(sys.executable, execdst)
            else:
                if PYTHONFRAMEWORK:
                    # When we're using a python framework bin/python refers
                    # to a stub executable that we don't want use, we need
                    # the executable in Resources/Python.app
                    dpath = os.path.join(self._python_app, "Contents", "MacOS")
                    sfile = os.path.join(dpath, PYTHONFRAMEWORK)
                    if not os.path.exists(sfile):
                        sfile = os.path.join(dpath, "Python")
                    self.copy_file(sfile, execdst)
                    make_exec(execdst)

                elif os.path.exists(os.path.join(sys.prefix, ".Python")):
                    fn = os.path.join(
                        sys.prefix,
                        "lib",
                        "python%d.%d" % (sys.version_info[:2]),
                        "orig-prefix.txt",
                    )

                    if os.path.exists(fn):
                        if sys.version_info[0] == 2:
                            with open(fn, "rU") as fp:
                                prefix = fp.read().strip()
                        else:
                            with open(fn, "r") as fp:
                                prefix = fp.read().strip()

                    rest_path = os.path.normpath(sys.executable)[
                        len(os.path.normpath(sys.prefix)) + 1 :  # noqa: E203
                    ]
                    if rest_path.startswith("."):
                        rest_path = rest_path[1:]

                    self.copy_file(os.path.join(prefix, rest_path), execdst)
                    make_exec(execdst)

                else:
                    self.copy_file(sys.executable, execdst)
                    make_exec(execdst)

            if not self.debug_skip_macholib:
                if self.force_system_tk:
                    print("force system tk")
                    resdir = os.path.join(dst, "Contents", "Resources")
                    pydir = os.path.join(
                        resdir, "lib", "python%s.%s" % (sys.version_info[:2])
                    )
                    ext_dir = os.path.join(pydir, os.path.basename(self.ext_dir))
                    tkinter_path = os.path.join(ext_dir, "_tkinter.so")
                    if os.path.exists(tkinter_path):
                        rewrite_tkinter_load_commands(tkinter_path)
                    else:
                        print("tkinter not found at", tkinter_path)

                mm = PythonStandalone(
                    appbuilder=self,
                    base=dst,
                    ext_dir=os.path.join(
                        dst,
                        "Contents",
                        "Resources",
                        "lib",
                        "python%s.%s" % (sys.version_info[:2]),
                        "lib-dynload",
                    ),
                    copyexts=copyexts,
                    executable_path=exp,
                )

                dylib, runtime = self.get_runtime()
                if self.semi_standalone:
                    mm.excludes.append(runtime)
                else:
                    mm.mm.run_file(runtime)
                for exclude in self.dylib_excludes:
                    info = macholib.dyld.framework_info(exclude)
                    if info is not None:
                        exclude = os.path.join(
                            info["location"], info["shortname"] + ".framework"
                        )
                    mm.excludes.append(exclude)
                for fmwk in self.frameworks:
                    mm.mm.run_file(fmwk)
                platfiles = mm.run()

                if self.strip:
                    platfiles = self.strip_dsym(platfiles)
                    self.strip_files(platfiles)

                arch = (
                    self.arch
                    if self.arch is not None
                    else get_platform().split("-")[-1]
                )

                if arch in ("universal2", "arm64"):
                    codesign_adhoc(target.appdir)
            self.app_files.append(dst)

    def copy_package_data(self, package, target_dir):
        """
        Copy any package data in a python package into the target_dir.

        This is a bit of a hack, it would be better to identify python eggs
        and copy those in whole.
        """
        exts = [i[0] for i in imp.get_suffixes()]
        exts.append(".py")
        exts.append(".pyc")
        exts.append(".pyo")

        def datafilter(item):
            for e in exts:
                if item.endswith(e):
                    return False
            return True

        target_dir = os.path.join(target_dir, *(package.identifier.split(".")))
        for dname in package.packagepath:
            filenames = list(filter(datafilter, zipio.listdir(dname)))
            for fname in filenames:
                if fname in (".svn", "CVS", ".hg", ".git"):
                    # Scrub revision manager junk
                    continue
                if fname in ("__pycache__",):
                    # Ignore PEP 3147 bytecode cache
                    continue
                if fname.startswith(".") and fname.endswith(".swp"):
                    # Ignore vim(1) temporary files
                    continue
                if fname.endswith("~") or fname.endswith(".orig"):
                    # Ignore backup files for common tools (hg, emacs, ...)
                    continue
                pth = os.path.join(dname, fname)

                # Check if we have found a package, exclude those
                if zipio.isdir(pth):
                    for p in zipio.listdir(pth):
                        if p.startswith("__init__.") and p[8:] in exts:
                            break

                    else:
                        if os.path.isfile(pth):
                            # Avoid extracting a resource file that happens
                            # to be zipfile.
                            copy_file(pth, os.path.join(target_dir, fname))
                        else:
                            copy_tree(pth, os.path.join(target_dir, fname))
                    continue

                elif zipio.isdir(pth) and (
                    zipio.isfile(os.path.join(pth, "__init__.py"))
                    or zipio.isfile(os.path.join(pth, "__init__.pyc"))
                    or zipio.isfile(os.path.join(pth, "__init__.pyo"))
                ):
                    # Subdirectory is a python package, these will get
                    # included later on when the subpackage itself is
                    # included, ignore for now.
                    pass

                else:
                    copy_file(pth, os.path.join(target_dir, fname))

    def strip_dsym(self, platfiles):
        """Remove .dSYM directories in the bundled application"""

        #
        # .dSYM directories are contain detached debugging information and
        # should be completely removed when the "strip" option is specified.
        #
        if self.dry_run:
            return platfiles
        for dirpath, dnames, _fnames in os.walk(self.appdir):
            for nm in list(dnames):
                if nm.endswith(".dSYM"):
                    print("removing debug info: %s/%s" % (dirpath, nm))
                    shutil.rmtree(os.path.join(dirpath, nm))
                    dnames.remove(nm)
        return [file for file in platfiles if ".dSYM" not in file]

    def strip_files(self, files):
        unstripped = 0
        stripfiles = []
        for fn in files:
            unstripped += os.stat(fn).st_size
            stripfiles.append(fn)
            log.info("stripping %s", os.path.basename(fn))
        strip_files(stripfiles, dry_run=self.dry_run, verbose=self.verbose)
        stripped = 0
        for fn in stripfiles:
            stripped += os.stat(fn).st_size
        log.info(
            "stripping saved %d bytes (%d / %d)",
            unstripped - stripped,
            stripped,
            unstripped,
        )

    def copy_dylib(self, src, dst):
        # will be copied from the framework?
        if src != sys.executable:
            force, self.force = self.force, True
            self.copy_file(src, dst)
            self.force = force
        return dst

    def copy_versioned_framework(self, info, dst):
        # Boy is this ugly, but it makes sense because the developer
        # could have both Python 2.3 and 2.4, or Tk 8.4 and 8.5, etc.
        # Saves a good deal of space, and I'm pretty sure this ugly
        # hack is correct in the general case.
        version = info["version"]
        if version is None:
            return self.raw_copy_framework(info, dst)
        short = info["shortname"] + ".framework"
        infile = os.path.join(info["location"], short)
        outfile = os.path.join(dst, short)
        vsplit = os.path.join(infile, "Versions").split(os.sep)

        def condition(src, vsplit=vsplit, version=version):
            srcsplit = src.split(os.sep)
            if (
                len(srcsplit) > len(vsplit)
                and srcsplit[: len(vsplit)] == vsplit
                and srcsplit[len(vsplit)] != version
                and not os.path.islink(src)
            ):
                return False

            # Skip Headers, .svn, and CVS dirs
            return framework_copy_condition(src)

        return self.copy_tree(
            infile, outfile, preserve_symlinks=True, condition=condition
        )

    def copy_framework(self, info, dst):
        force, self.force = self.force, True
        if info["shortname"] == PYTHONFRAMEWORK:
            self.copy_python_framework(info, dst)
        else:
            self.copy_versioned_framework(info, dst)
        self.force = force
        return os.path.join(dst, info["name"])

    def raw_copy_framework(self, info, dst):
        short = info["shortname"] + ".framework"
        infile = os.path.join(info["location"], short)
        outfile = os.path.join(dst, short)
        return self.copy_tree(
            infile, outfile, preserve_symlinks=True, condition=framework_copy_condition
        )

    def copy_python_framework(self, info, dst):
        # In this particular case we know exactly what we can
        # get away with.. should this be extended to the general
        # case?  Per-framework recipes?
        includedir = get_config_var("CONFINCLUDEPY")
        configdir = get_config_var("LIBPL")

        if includedir is None:
            includedir = "python%d.%d" % (sys.version_info[:2])
        else:
            includedir = os.path.basename(includedir)
            if includedir == "Headers":
                # This is a copy of Python as shipped with Xcode
                includedir = "python%d.%d%s" % (sys.version_info[:2] + (sys.abiflags,))

        if configdir is None:
            configdir = "config"
        else:
            configdir = os.path.basename(configdir)

        indir = os.path.dirname(os.path.join(info["location"], info["name"]))
        outdir = os.path.dirname(os.path.join(dst, info["name"]))
        if os.path.exists(outdir):
            # Python framework has already been created.
            return

        self.mkpath(os.path.join(outdir, "Resources"))
        pydir = "python%s.%s" % (sys.version_info[:2])

        # Create a symlink "for Python.frameworks/Versions/Current". This
        # is required for the Mac App-store.
        make_symlink(
            os.path.basename(outdir), os.path.join(os.path.dirname(outdir), "Current")
        )

        # Likewise for two links in the root of the framework:
        make_symlink(
            "Versions/Current/Resources",
            os.path.join(os.path.dirname(os.path.dirname(outdir)), "Resources"),
        )
        make_symlink(
            os.path.join("Versions/Current", PYTHONFRAMEWORK),
            os.path.join(os.path.dirname(os.path.dirname(outdir)), PYTHONFRAMEWORK),
        )

        # Experiment for issue 57
        if not os.path.exists(os.path.join(indir, "include")):
            alt = os.path.join(indir, "Versions/Current")
            if os.path.exists(os.path.join(alt, "include")):
                indir = alt

        # distutils looks for some files relative to sys.executable, which
        # means they have to be in the framework...
        self.mkpath(os.path.join(outdir, "include"))
        self.mkpath(os.path.join(outdir, "include", includedir))
        self.mkpath(os.path.join(outdir, "lib"))
        self.mkpath(os.path.join(outdir, "lib", pydir))
        self.mkpath(os.path.join(outdir, "lib", pydir, configdir))

        fmwkfiles = [
            os.path.basename(info["name"]),
            "Resources/Info.plist",
            "include/%s/pyconfig.h" % (includedir),
        ]
        if "_sysconfigdata" not in sys.modules:
            fmwkfiles.append("lib/%s/%s/Makefile" % (pydir, configdir))

        for fn in fmwkfiles:
            self.copy_file(os.path.join(indir, fn), os.path.join(outdir, fn))

    def fixup_distribution(self):
        dist = self.distribution

        # Trying to obtain app and plugin from dist for backward compatibility
        # reasons.
        app = dist.app
        plugin = dist.plugin
        # If we can get suitable values from self.app and self.plugin,
        # we prefer them.
        if self.app is not None or self.plugin is not None:
            app = self.app
            plugin = self.plugin

        # Convert our args into target objects.
        dist.app = FixupTargets(app, "script")
        dist.plugin = FixupTargets(plugin, "script")
        if dist.app and dist.plugin:
            raise DistutilsOptionError(
                "You must specify either app or plugin, not both"
            )
        elif dist.app:
            self.style = "app"
            self.targets = dist.app
        elif dist.plugin:
            self.style = "plugin"
            self.targets = dist.plugin
        else:
            raise DistutilsOptionError("You must specify either app or plugin")
        if len(self.targets) != 1:
            raise DistutilsOptionError("Multiple targets not currently supported")
        if not self.extension:
            self.extension = "." + self.style

        # make sure all targets use the same directory, this is
        # also the directory where the pythonXX.dylib must reside
        paths = set()
        for target in self.targets:
            paths.add(os.path.dirname(target.get_dest_base()))

        if len(paths) > 1:
            raise DistutilsOptionError(
                "all targets must use the same directory: %s" % (list(paths),)
            )
        if paths:
            app_dir = paths.pop()  # the only element
            if os.path.isabs(app_dir):
                raise DistutilsOptionError(
                    "app directory must be relative: %s" % (app_dir,)
                )
            self.app_dir = os.path.join(self.dist_dir, app_dir)
            self.mkpath(self.app_dir)
        else:
            # Do we allow to specify no targets?
            # We can at least build a zipfile...
            self.app_dir = self.lib_dir

    def initialize_prescripts(self):
        prescripts = []
        prescripts.append("reset_sys_path")
        if self.semi_standalone:
            prescripts.append("semi_standalone_path")

        if 0 and sys.version_info[:2] >= (3, 2) and not self.alias:
            # Python 3.2 or later requires a more complicated
            # bootstrap
            prescripts.append("import_encodings")

        if os.path.exists(os.path.join(sys.prefix, "pyvenv.cfg")):
            # We're in a venv, which means sys.path
            # will be broken in alias builds unless we fix
            # it.
            real_prefix = None
            global_site_packages = False
            with open(os.path.join(sys.prefix, "pyvenv.cfg")) as fp:

                for ln in fp:
                    if ln.startswith("home = "):
                        _, home_path = ln.split("=", 1)
                        real_prefix = os.path.dirname(home_path.strip())

                    elif ln.startswith("include-system-site-packages = "):
                        _, global_site_packages = ln.split("=", 1)
                        global_site_packages = global_site_packages == "true"

            if real_prefix is None:
                raise DistutilsPlatformError(
                    "Pyvenv detected, cannot determine base prefix"
                )

            if self.site_packages or self.alias:
                print("Add paths for VENV", real_prefix, global_site_packages)
                prescripts.append("virtualenv_site_packages")
                prescripts.append(
                    StringIO(
                        "_site_packages(%r, %r, %d)"
                        % (sys.prefix, real_prefix, global_site_packages)
                    )
                )

        elif os.path.exists(os.path.join(sys.prefix, ".Python")):
            # We're in a virtualenv, which means sys.path
            # will be broken in alias builds unless we fix
            # it.
            if self.alias or self.semi_standalone:
                prescripts.append("virtualenv")
                prescripts.append(
                    StringIO("_fixup_virtualenv(%r)" % (sys.real_prefix,))
                )

            if self.site_packages or self.alias:
                import site

                global_site_packages = not os.path.exists(
                    os.path.join(
                        os.path.dirname(site.__file__), "no-global-site-packages.txt"
                    )
                )

                prescripts.append("virtualenv_site_packages")
                prescripts.append(
                    StringIO(
                        "_site_packages(%r, %r, %d)"
                        % (sys.prefix, sys.real_prefix, global_site_packages)
                    )
                )

        elif self.site_packages or self.alias:
            prescripts.append("site_packages")

        if is_system():
            prescripts.append("system_path_extras")

        included_subpkg = [pkg for pkg in self.packages if "." in pkg]
        if included_subpkg:
            prescripts.append("setup_included_subpackages")
            prescripts.append(StringIO("_path_hooks = %r" % (included_subpkg)))

        if self.emulate_shell_environment:
            prescripts.append("emulate_shell_environment")

        if self.argv_emulation and self.style == "app":
            prescripts.append("argv_emulation")
            if "CFBundleDocumentTypes" not in self.plist:
                self.plist["CFBundleDocumentTypes"] = [
                    {
                        "CFBundleTypeOSTypes": ["****", "fold", "disk"],
                        "CFBundleTypeRole": "Viewer",
                    },
                ]

        if self.argv_inject is not None:
            prescripts.append("argv_inject")
            prescripts.append(StringIO("_argv_inject(%r)\n" % (self.argv_inject,)))

        if self.style == "app" and not self.no_chdir:
            prescripts.append("chdir_resource")
        if not self.alias:
            prescripts.append("disable_linecache")
            prescripts.append("boot_" + self.style)
        else:

            # Add ctypes prescript because it is needed to
            # find libraries in the bundle, but we don't run
            # recipes and hence the ctypes recipe is not used
            # for alias builds.
            prescripts.append("ctypes_setup")

            if self.additional_paths:
                prescripts.append("path_inject")
                prescripts.append(
                    StringIO("_path_inject(%r)\n" % (self.additional_paths,))
                )
            prescripts.append("boot_alias" + self.style)
        newprescripts = []
        for s in prescripts:
            if isinstance(s, basestring):
                newprescripts.append(self.get_bootstrap("py2app.bootstrap." + s))
            else:
                newprescripts.append(s)

        for target in self.targets:
            prescripts = getattr(target, "prescripts", [])
            target.prescripts = newprescripts + prescripts

    def get_bootstrap(self, bootstrap):
        if isinstance(bootstrap, basestring):
            if not os.path.exists(bootstrap):
                bootstrap = imp_find_module(bootstrap)[1]
        return bootstrap

    def get_bootstrap_data(self, bootstrap):
        bootstrap = self.get_bootstrap(bootstrap)
        if not isinstance(bootstrap, basestring):
            return bootstrap.getvalue()
        else:
            if sys.version_info[0] == 2:
                with open(bootstrap, "rU") as fp:
                    return fp.read()
            else:
                with open(bootstrap, "r") as fp:
                    return fp.read()

    def create_pluginbundle(self, target, script, use_runtime_preference=True):
        base = target.get_dest_base()
        appdir = os.path.join(self.dist_dir, os.path.dirname(base))
        appname = self.get_appname()
        print("*** creating plugin bundle: %s ***" % (appname,))
        if self.runtime_preferences and use_runtime_preference:
            self.plist.setdefault("PyRuntimeLocations", self.runtime_preferences)
        appdir, plist = create_pluginbundle(
            appdir,
            appname,
            plist=self.plist,
            extension=self.extension,
            arch=self.arch,
        )
        appdir = fsencoding(appdir)
        resdir = os.path.join(appdir, "Contents", "Resources")
        return appdir, resdir, plist

    def create_appbundle(self, target, script, use_runtime_preference=True):
        base = target.get_dest_base()
        appdir = os.path.join(self.dist_dir, os.path.dirname(base))
        appname = self.get_appname()
        print("*** creating application bundle: %s ***" % (appname,))
        if self.runtime_preferences and use_runtime_preference:
            self.plist.setdefault("PyRuntimeLocations", self.runtime_preferences)
        pythonInfo = self.plist.setdefault("PythonInfoDict", {})
        py2appInfo = pythonInfo.setdefault("py2app", {})
        py2appInfo.update({"alias": bool(self.alias)})
        appdir, plist = create_appbundle(
            appdir,
            appname,
            plist=self.plist,
            extension=self.extension,
            arch=self.arch,
            redirect_stdout=self.redirect_stdout_to_asl,
            use_old_sdk=self.use_old_sdk,
        )
        appdir = fsencoding(appdir)
        resdir = os.path.join(appdir, "Contents", "Resources")
        return appdir, resdir, plist

    def create_bundle(self, target, script, use_runtime_preference=True):
        fn = getattr(self, "create_%sbundle" % (self.style,))
        return fn(target, script, use_runtime_preference=use_runtime_preference)

    def iter_frameworks(self):
        for fn in self.frameworks:
            fmwk = macholib.dyld.framework_info(fn)
            if fmwk is None:
                yield fn
            else:
                basename = fmwk["shortname"] + ".framework"
                yield os.path.join(fmwk["location"], basename)

    def build_alias_executable(self, target, script, extra_scripts):
        # Build an alias executable for the target
        appdir, resdir, plist = self.create_bundle(target, script)

        # symlink python executable
        execdst = os.path.join(appdir, "Contents", "MacOS", "python")
        prefixPathExecutable = os.path.join(sys.prefix, "bin", "python")
        if os.path.exists(prefixPathExecutable):
            pyExecutable = prefixPathExecutable
        else:
            pyExecutable = sys.executable
        make_symlink(pyExecutable, execdst)

        # make PYTHONHOME
        pyhome = os.path.join(resdir, "lib", "python%d.%d" % (sys.version_info[:2]))
        realhome = os.path.join(
            sys.prefix, "lib", "python%d.%d" % (sys.version_info[:2])
        )
        makedirs(pyhome)
        if self.optimize:
            make_symlink("../../site.pyo", os.path.join(pyhome, "site.pyo"))
        else:
            make_symlink("../../site.pyc", os.path.join(pyhome, "site.pyc"))
        make_symlink(os.path.join(realhome, "config"), os.path.join(pyhome, "config"))

        # symlink data files
        for src, dest in self.iter_data_files():
            dest = os.path.join(resdir, dest)
            if src == dest:
                continue
            makedirs(os.path.dirname(dest))
            try:
                copy_resource(src, dest, dry_run=self.dry_run, symlink=1)
            except:  # noqa: E722,B001
                import traceback

                traceback.print_exc()
                raise

        plugindir = os.path.join(appdir, "Contents", "Library")
        for src, dest in self.iter_extra_plugins():
            dest = os.path.join(plugindir, dest)
            if src == dest:
                continue

            makedirs(os.path.dirname(dest))
            try:
                copy_resource(src, dest, dry_run=self.dry_run)
            except:  # noqa: E722,B001
                import traceback

                traceback.print_exc()
                raise

        # symlink frameworks
        for src in self.iter_frameworks():
            dest = os.path.join(appdir, "Contents", "Frameworks", os.path.basename(src))
            if src == dest:
                continue
            makedirs(os.path.dirname(dest))
            make_symlink(os.path.abspath(src), dest)

        self.compile_datamodels(resdir)
        self.compile_mappingmodels(resdir)

        bootfn = "__boot__"
        bootfile = open(os.path.join(resdir, bootfn + ".py"), "w")
        for fn in target.prescripts:
            bootfile.write(self.get_bootstrap_data(fn))
            bootfile.write("\n\n")
        bootfile.write("DEFAULT_SCRIPT=%r\n" % (os.path.realpath(script),))
        script_map = {}
        for fn in extra_scripts:
            tgt = os.path.realpath(fn)
            fn = os.path.basename(fn)
            if fn.endswith(".py"):
                script_map[fn[:-3]] = tgt
            elif fn.endswith(".py"):
                script_map[fn[:-4]] = tgt
            else:
                script_map[fn] = tgt

        bootfile.write("SCRIPT_MAP=%r\n" % (script_map,))
        bootfile.write("try:\n")
        bootfile.write("    _run()\n")
        bootfile.write("except KeyboardInterrupt:\n")
        bootfile.write("    pass\n")
        bootfile.close()

        target.appdir = appdir
        return appdir

    def copy_loader_paths(self, sourcefn, destfn):
        todo = [(sourcefn, destfn)]

        while todo:
            next = []
            for item in todo:
                for s, d in loader_paths(*item):
                    if os.path.exists(d):
                        continue
                    next.append((s, d))
                    if not self.dry_run:
                        if not os.path.exists(os.path.dirname(d)):
                            os.makedirs(os.path.dirname(d))
                    copy_file(s, d, dry_run=self.dry_run)
            todo = next

    def build_executable(
        self, target, arcname, pkgexts, copyexts, script, extra_scripts
    ):
        # Build an executable for the target
        appdir, resdir, plist = self.create_bundle(target, script)
        self.appdir = appdir
        self.resdir = resdir
        self.plist = plist

        for fn in extra_scripts:
            if fn.endswith(".py"):
                fn = fn[:-3]
            elif fn.endswith(".pyw"):
                fn = fn[:-4]

            src_fn = script_executable(
                arch=self.arch, secondary=False, use_old_sdk=self.use_old_sdk
            )
            tgt_fn = os.path.join(
                self.appdir, "Contents", "MacOS", os.path.basename(fn)
            )
            mergecopy(src_fn, tgt_fn)
            make_exec(tgt_fn)

        site_path = os.path.join(resdir, "site.py")
        byte_compile(
            [SourceModule("site", site_path)],
            target_dir=resdir,
            optimize=self.optimize,
            force=self.force,
            verbose=self.verbose,
            dry_run=self.dry_run,
        )
        if not self.dry_run:
            os.unlink(site_path)

        includedir = get_config_var("CONFINCLUDEPY")
        configdir = get_config_var("LIBPL")

        if includedir is None:
            includedir = "python%d.%d" % (sys.version_info[:2])
        else:
            includedir = os.path.basename(includedir)

        if configdir is None:
            configdir = "config"
        else:
            configdir = os.path.basename(configdir)

        self.compile_datamodels(resdir)
        self.compile_mappingmodels(resdir)

        bootfn = "__boot__"
        bootfile = open(os.path.join(resdir, bootfn + ".py"), "w")
        for fn in target.prescripts:
            bootfile.write(self.get_bootstrap_data(fn))
            bootfile.write("\n\n")

        bootfile.write("DEFAULT_SCRIPT=%r\n" % (os.path.basename(script),))

        script_map = {}
        for fn in extra_scripts:
            fn = os.path.basename(fn)
            if fn.endswith(".py"):
                script_map[fn[:-3]] = fn
            elif fn.endswith(".py"):
                script_map[fn[:-4]] = fn
            else:
                script_map[fn] = fn

        bootfile.write("SCRIPT_MAP=%r\n" % (script_map,))
        bootfile.write("_run()\n")
        bootfile.close()

        self.copy_file(script, resdir)
        for fn in extra_scripts:
            self.copy_file(fn, resdir)

        pydir = os.path.join(resdir, "lib", "python%s.%s" % (sys.version_info[:2]))

        if sys.version_info[0] == 2 or self.semi_standalone:
            arcdir = os.path.join(resdir, "lib", "python%d.%d" % (sys.version_info[:2]))
        else:
            arcdir = os.path.join(resdir, "lib")
        realhome = os.path.join(
            sys.prefix, "lib", "python%d.%d" % (sys.version_info[:2])
        )
        self.mkpath(pydir)

        # The site.py file needs to be a two locations
        # 1) in lib/pythonX.Y, to be found during normal startup and
        #    by the 'python' executable
        # 2) in the resources directory next to the script for
        #    semistandalone builds (the lib/pythonX.Y directory is too
        #    late on sys.path to be found in that case).
        #
        if self.optimize:
            make_symlink("../../site.pyo", os.path.join(pydir, "site.pyo"))
        else:
            make_symlink("../../site.pyc", os.path.join(pydir, "site.pyc"))
        cfgdir = os.path.join(pydir, configdir)
        realcfg = os.path.join(realhome, configdir)
        real_include = os.path.join(sys.prefix, "include")
        if self.semi_standalone:
            make_symlink(realcfg, cfgdir)
            make_symlink(real_include, os.path.join(resdir, "include"))
        else:
            self.mkpath(cfgdir)
            if "_sysconfigdata" not in sys.modules:
                # Recent enough versions of Python 2.7 and 3.x have
                # an _sysconfigdata module and don't need the Makefile
                # to provide the sysconfig data interface. Don't copy
                # them.
                for fn in "Makefile", "Setup", "Setup.local", "Setup.config":
                    rfn = os.path.join(realcfg, fn)
                    if os.path.exists(rfn):
                        self.copy_file(rfn, os.path.join(cfgdir, fn))

            inc_dir = os.path.join(resdir, "include", includedir)
            self.mkpath(inc_dir)
            self.copy_file(get_config_h_filename(), os.path.join(inc_dir, "pyconfig.h"))

        self.copy_file(arcname, arcdir)
        if sys.version_info[0] != 2:
            import zlib

            self.copy_file(zlib.__file__, os.path.dirname(arcdir))

        ext_dir = os.path.join(pydir, os.path.basename(self.ext_dir))
        self.copy_tree(self.ext_dir, ext_dir, preserve_symlinks=True)
        self.copy_tree(
            self.framework_dir,
            os.path.join(appdir, "Contents", "Frameworks"),
            preserve_symlinks=True,
        )
        for pkg_name in self.packages:
            pkg = self.get_bootstrap(pkg_name)

            if self.semi_standalone:
                # For semi-standalone builds don't copy packages
                # from the stdlib into the app bundle, even when
                # they are mentioned in self.packages.
                p = Package(pkg_name, pkg)
                if not not_stdlib_filter(p):
                    continue

            dst = os.path.join(pydir, pkg_name)
            if os.path.isdir(pkg):
                self.mkpath(dst)
                self.copy_tree(pkg, dst)
            else:
                self.copy_file(pkg, dst + ".py")

            # The python files should be bytecompiled
            # here (see issue 101)

        for copyext in copyexts:
            fn = os.path.join(
                ext_dir,
                (
                    copyext.identifier.replace(".", os.sep)
                    + os.path.splitext(copyext.filename)[1]
                ),
            )
            self.mkpath(os.path.dirname(fn))
            copy_file(copyext.filename, fn, dry_run=self.dry_run)

            # MachoStandalone does not support '@loader_path' (and cannot in its
            # current form). Check for "@loader_path" in the load commands of
            # the extension and copy those files into the bundle as well.
            self.copy_loader_paths(copyext.filename, fn)

        for src, dest in self.iter_data_files():
            dest = os.path.join(resdir, dest)
            if src == dest:
                continue
            makedirs(os.path.dirname(dest))
            copy_resource(src, dest, dry_run=self.dry_run)

        plugindir = os.path.join(appdir, "Contents", "Library")
        for src, dest in self.iter_extra_plugins():
            dest = os.path.join(plugindir, dest)
            if src == dest:
                continue

            makedirs(os.path.dirname(dest))
            copy_resource(src, dest, dry_run=self.dry_run)

        target.appdir = appdir
        return appdir

    def create_loader(self, item):
        # Hm, how to avoid needless recreation of this file?
        slashname = item.identifier.replace(".", os.sep)
        pathname = os.path.join(self.temp_dir, "%s.py" % slashname)
        if os.path.exists(pathname):
            if self.verbose:
                print("skipping python loader for extension %r" % (item.identifier,))
        else:
            self.mkpath(os.path.dirname(pathname))
            # and what about dry_run?
            if self.verbose:
                print("creating python loader for extension %r" % (item.identifier,))

            fname = slashname + os.path.splitext(item.filename)[1]
            source = make_loader(fname)
            if not self.dry_run:
                with open(pathname, "w") as fp:
                    fp.write(source)
            else:
                return
        return SourceModule(item.identifier, pathname)

    def make_lib_archive(self, zip_filename, base_dir, verbose=0, dry_run=0):
        # Like distutils "make_archive", except we can specify the
        # compression to use - default is ZIP_STORED to keep the
        # runtime performance up.
        # Also, we don't append '.zip' to the filename.
        from distutils.dir_util import mkpath

        mkpath(os.path.dirname(zip_filename), dry_run=dry_run)

        if self.compressed:
            compression = zipfile.ZIP_DEFLATED
        else:
            compression = zipfile.ZIP_STORED
        if not dry_run:
            z = zipfile.ZipFile(zip_filename, "w", compression=compression)
            save_cwd = os.getcwd()
            os.chdir(base_dir)
            for dirpath, _dirnames, filenames in os.walk("."):
                if filenames:
                    # Ensure that there are directory entries for
                    # all directories in the zipfile. This is a
                    # workaround for <http://bugs.python.org/issue14905>:
                    # zipimport won't consider 'pkg/foo.py' to be in
                    # namespace package 'pkg' unless there is an
                    # entry for the directory (or there is a
                    # pkg/__init__.py file as well)
                    z.write(dirpath, dirpath)

                for fn in filenames:
                    path = os.path.normpath(os.path.join(dirpath, fn))
                    if os.path.isfile(path):
                        z.write(path, path)

            os.chdir(save_cwd)
            z.close()

        return zip_filename

    def copy_tree(
        self,
        infile,
        outfile,
        preserve_mode=1,
        preserve_times=1,
        preserve_symlinks=0,
        level=1,
        condition=None,
    ):
        """Copy an entire directory tree respecting verbose, dry-run,
        and force flags.

        This version doesn't bork on existing symlinks
        """
        return copy_tree(
            infile,
            outfile,
            preserve_mode,
            preserve_times,
            preserve_symlinks,
            not self.force,
            dry_run=self.dry_run,
            condition=condition,
        )

    def copy_file(self, infile, outfile):
        """
        This version doesn't bork on existing symlinks
        """
        return copy_file(infile, outfile)
