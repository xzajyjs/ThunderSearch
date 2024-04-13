import os


def check(cmd, mf):
    m = mf.findNode("zmq")
    if m is None or m.filename is None:
        return None

    dylibs = os.scandir(os.path.join(m.packagepath[0], ".dylibs"))
    frameworks = [lib.path for lib in dylibs]

    return {"frameworks": frameworks}
