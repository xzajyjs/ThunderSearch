import os
import sys
import textwrap

if sys.version_info[0] == 2:
    from cStringIO import StringIO
else:
    from io import StringIO

PRESCRIPT = textwrap.dedent(
    """\
    import pkg_resources, zipimport, os

    def find_eggs_in_zip(importer, path_item, only=False):
        if importer.archive.endswith('.whl'):
            # wheels are not supported with this finder
            # they don't have PKG-INFO metadata, and won't ever contain eggs
            return

        metadata = pkg_resources.EggMetadata(importer)
        if metadata.has_metadata('PKG-INFO'):
            yield Distribution.from_filename(path_item, metadata=metadata)
        for subitem in metadata.resource_listdir(''):
            if not only and pkg_resources._is_egg_path(subitem):
                subpath = os.path.join(path_item, subitem)
                dists = find_eggs_in_zip(zipimport.zipimporter(subpath), subpath)
                for dist in dists:
                    yield dist
            elif subitem.lower().endswith(('.dist-info', '.egg-info')):
                subpath = os.path.join(path_item, subitem)
                submeta = pkg_resources.EggMetadata(zipimport.zipimporter(subpath))
                submeta.egg_info = subpath
                yield pkg_resources.Distribution.from_location(path_item, subitem, submeta)  # noqa: B950

    def _fixup_pkg_resources():
        pkg_resources.register_finder(zipimport.zipimporter, find_eggs_in_zip)
        pkg_resources.working_set.entries = []
        list(map(pkg_resources.working_set.add_entry, sys.path))

    _fixup_pkg_resources()
"""
)


def check(cmd, mf):
    m = mf.findNode("pkg_resources")
    if m is None or m.filename is None:
        return None

    if m.filename.endswith("__init__.py"):
        vendor_dir = os.path.join(os.path.dirname(m.filename), "_vendor")
    else:
        vendor_dir = os.path.join(m.filename, "_vendor")

    expected_missing_imports = {
        "__main__.__requires__",
    }

    if os.path.exists(vendor_dir):
        for topdir, dirs, files in os.walk(vendor_dir):
            for fn in files:
                if fn in ("__pycache__", "__init__.py"):
                    continue

                relnm = os.path.relpath(os.path.join(topdir, fn), vendor_dir)
                if relnm.endswith(".py"):
                    relnm = relnm[:-3]
                relnm = relnm.replace("/", ".")

                if fn.endswith(".py"):
                    mf.import_hook("pkg_resources._vendor." + relnm, m, ["*"])
                    expected_missing_imports.add("pkg_resources.extern." + relnm)
            for dn in dirs:
                if not os.path.exists(os.path.join(topdir, dn, "__init__.py")):
                    continue
                relnm = os.path.relpath(os.path.join(topdir, dn), vendor_dir)
                relnm = relnm.replace("/", ".")

                mf.import_hook("pkg_resources._vendor." + relnm, m, ["*"])
                expected_missing_imports.add("pkg_resources.extern." + relnm)

        mf.import_hook("pkg_resources._vendor", m)

    if sys.version[0] != 2:
        expected_missing_imports.add("__builtin__")

    return {
        "expected_missing_imports": expected_missing_imports,
        "prescripts": [StringIO(PRESCRIPT)],
    }
