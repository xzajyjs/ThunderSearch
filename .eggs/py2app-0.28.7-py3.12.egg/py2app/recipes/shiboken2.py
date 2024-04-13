def check(cmd, mf):
    name = "shiboken2"
    m = mf.findNode(name)
    if m is None or m.filename is None:
        return None

    mf.import_hook("shiboken2.support", m, ["*"])
    mf.import_hook("shiboken2.support.signature", m, ["*"])
    mf.import_hook("shiboken2.support.signature.lib", m, ["*"])

    return None
