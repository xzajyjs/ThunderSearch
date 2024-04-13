def check(cmd, mf):
    m = mf.findNode("pandas")
    if m is None or m.filename is None:
        return None

    includes = ["pandas._libs.tslibs.base"]

    return {"includes": includes}
