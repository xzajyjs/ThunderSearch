def check(cmd, mf):
    print("CTYPES USERS", list(mf.getReferers("ctypes")))
    m = mf.findNode("ctypes")
    if m is None or m.filename is None:
        return None

    return {"prescripts": ["py2app.bootstrap.ctypes_setup"]}
