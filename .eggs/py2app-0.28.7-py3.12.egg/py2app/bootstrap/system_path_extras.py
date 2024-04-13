""" Add Apple's additional packages to sys.path """


def add_system_python_extras():
    import site
    import sys

    ver = "%s.%s" % (sys.version_info[:2])

    site.addsitedir(
        "/System/Library/Frameworks/Python.framework/Versions/"
        "%s/Extras/lib/python" % (ver,)
    )


add_system_python_extras()
