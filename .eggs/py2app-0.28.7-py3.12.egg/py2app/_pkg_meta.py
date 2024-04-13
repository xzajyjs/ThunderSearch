import os

IGNORED_DISTINFO = set(["installed-files.txt", "RECORD"])  # noqa: C405


def update_metadata_cache_distinfo(infos, dist_info_path):
    """
    Update mapping from filename to dist_info directory
    for all files installed by the package described
    in dist_info
    """
    fn = os.path.join(dist_info_path, "installed-files.txt")
    if os.path.exists(fn):
        with open(fn, "r") as stream:
            for line in stream:
                infos[
                    os.path.realpath(os.path.join(dist_info_path, line.rstrip()))
                ] = dist_info_path

    fn = os.path.join(dist_info_path, "RECORD")
    if os.path.exists(fn):
        with open(fn, "r") as stream:
            for ln in stream:
                # The RECORD file is a CSV file according to PEP 376, but
                # the wheel spec is silent on this and the wheel tool
                # creates files that aren't necessarily correct CSV files
                # (See issue #280 at https://github.com/pypa/wheel)
                #
                # This code works for all filenames, except those containing
                # line seperators.
                relpath = ln.rsplit(",", 2)[0]

                if relpath.startswith('"') and relpath.endswith('"'):
                    # The record file is a CSV file that can contain quoted strings.
                    relpath = relpath[1:-1].replace('""', '"')

                infos[
                    os.path.realpath(
                        os.path.join(os.path.dirname(dist_info_path), relpath)
                    )
                ] = dist_info_path


def update_metadata_cache_distlink(infos, dist_link_path):
    """
    Update mapping from filename to dist_info directory
    for all files in the package installed in editable mode.

    *dist_link_path* is the .egg-link file for the package
    """
    # An editable install does not contain a listing of installed
    # files.
    with open(dist_link_path, "r") as fp:
        dn = fp.readline()[:-1]

    # The list of files and directories that would have been
    # in the list of installed items.
    to_include = []

    # First look for the dist-info for this editable install
    for fn in os.listdir(dn):
        if fn.endswith(".egg-info") or fn.endswith(".dist-info"):
            dist_info_path = os.path.join(dn, fn)
            to_include.append(dist_info_path)
            try:
                with open(os.path.join(dist_info_path, "top_level.txt"), "r") as fp:
                    toplevels = fp.read().splitlines()
            except OSError:
                continue
            break
    else:
        # No dist-info for this install
        return

    # Then look for the toplevels for this package
    for fn in os.listdir(dn):
        if fn in toplevels or fn.rstrip(".py") in toplevels:
            to_include.append(os.path.join(dn, fn))

    # Finally recursively add all items found to
    # the cache.
    add_recursive(infos, dist_info_path, to_include)


def add_recursive(infos, dist_info_path, to_include):
    """Add items from to_include to infos, recursively
    walking into directories"""
    for item in to_include:
        if os.path.isdir(item):
            add_recursive(
                infos,
                dist_info_path,
                [os.path.join(item, fn) for fn in os.listdir(item)],
            )

        else:
            infos[item] = dist_info_path


def scan_for_metadata(path):
    """
    Scan the importlib search path *path* for dist-info/egg-info
    directories and return a mapping from absolute paths of installed
    files to their egg-info location
    """
    infos = {}
    for dirname in path:
        if not os.path.isdir(dirname):
            continue
        for nm in os.listdir(dirname):
            if nm.endswith(".egg-link"):
                # Editable install, these will be found later on in
                # *path* as well, but contain metadata without a list
                # of installed files.
                update_metadata_cache_distlink(infos, os.path.join(dirname, nm))

            elif nm.endswith(".egg-info") or nm.endswith(".dist-info"):
                update_metadata_cache_distinfo(infos, os.path.join(dirname, nm))

    return infos
