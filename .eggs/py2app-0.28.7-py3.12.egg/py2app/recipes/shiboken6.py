def check(cmd, mf):
    name = "shiboken6"
    m = mf.findNode(name)
    if m is None or m.filename is None:
        return None

    mf.import_hook("shiboken6.support", m, ["*"])
    mf.import_hook("shiboken6.support.signature", m, ["*"])
    mf.import_hook("shiboken6.support.signature.lib", m, ["*"])

    return {"packages": ["shiboken6"]}
