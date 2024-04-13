import sys


def check(cmd, mf):
    if sys.version_info[:2] >= (3, 6):
        # As of Python 3.6 the sysconfig module
        # dynamicly imports a module using the
        # __import__ function.
        m = mf.findNode("sysconfig")
        if m is not None:
            import sysconfig

            mf.import_hook(sysconfig._get_sysconfigdata_name(), m)

    else:
        return None
