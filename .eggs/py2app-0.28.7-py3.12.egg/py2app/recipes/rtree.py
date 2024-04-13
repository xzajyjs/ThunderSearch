import os


def check(cmd, mf):
    m = mf.findNode("rtree")
    if m is None or m.filename is None:
        return None

    try:
        rtree_dylibs = os.scandir(os.path.join(m.packagepath[0], "lib"))
    except OSError:
        return None

    frameworks = [lib.path for lib in rtree_dylibs]

    return {"frameworks": frameworks}
