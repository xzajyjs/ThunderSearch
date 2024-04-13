import sys

from modulegraph.modulegraph import MissingModule


def check(cmd, mf):
    if sys.version_info[0] != 2:
        return {}

    # ftplib has an optional dependency on an external (and likely
    # non-existing) SOCKS module.
    f = mf.findNode("ftplib")
    m = mf.findNode("SOCKS")
    if m is not None and f is not None and isinstance(m, MissingModule):
        mf.removeReference(f, m)

    return {}
