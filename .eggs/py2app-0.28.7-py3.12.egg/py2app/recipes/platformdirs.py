def check(cmd, mf):
    m = mf.findNode("platformdirs")
    if m is None or m.filename is None:
        return None

    includes = ["platformdirs.macos"]

    return {"includes": includes}
