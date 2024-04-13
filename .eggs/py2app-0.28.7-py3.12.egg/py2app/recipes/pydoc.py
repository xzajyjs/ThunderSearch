def check(cmd, mf):
    m = mf.findNode("pydoc")
    if m is None or m.filename is None:
        return None
    refs = [
        "Tkinter",
        "tty",
        "BaseHTTPServer",
        "mimetools",
        "select",
        "threading",
        "ic",
        "getopt",
        "tkinter",
        "win32",
    ]
    for ref in refs:
        mf.removeReference(m, ref)
    return {}
