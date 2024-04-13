import re
import sys

cookie_re = re.compile(br"coding[:=]\s*([-\w.]+)")
if sys.version_info[0] == 2:
    default_encoding = "ascii"
else:
    default_encoding = "utf-8"


def guess_encoding(fp):
    for _i in range(2):
        ln = fp.readline()

        m = cookie_re.search(ln)
        if m is not None:
            return m.group(1).decode("ascii")

    return default_encoding


def _run():
    global __file__
    import os
    import site  # noqa: F401

    sys.frozen = "macosx_app"

    argv0 = os.path.basename(os.environ["ARGVZERO"])
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)  # noqa: F821

    sys.argv[0] = __file__ = script
    if sys.version_info[0] == 2:
        with open(script, "rU") as fp:
            source = fp.read() + "\n"
    else:
        with open(script, "rb") as fp:
            encoding = guess_encoding(fp)

        with open(script, "r", encoding=encoding) as fp:
            source = fp.read() + "\n"

        BOM = b"\xef\xbb\xbf".decode("utf-8")

        if source.startswith(BOM):
            source = source[1:]

    exec(compile(source, script, "exec"), globals(), globals())
