def check(cmd, mf):
    m = mf.findNode("sphinx")
    if m is None or m.filename is None:
        return None

    includes = [
        "sphinxcontrib.applehelp",
        "sphinxcontrib.devhelp",
        "sphinxcontrib.htmlhelp",
        "sphinxcontrib.jsmath",
        "sphinxcontrib.qthelp",
        "sphinxcontrib.serializinghtml",
    ]

    return {"includes": includes}
