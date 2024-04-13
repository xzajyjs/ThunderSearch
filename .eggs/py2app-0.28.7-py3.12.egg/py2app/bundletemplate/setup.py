import distutils.sysconfig
import distutils.util
import os
import re
import sys

gPreBuildVariants = [
    {
        "name": "main-universal2",
        "target": "10.9",
        "cflags": "-g -arch arm64 -arch x86_64",
        "cc": "/usr/bin/clang",
    },
    {
        "name": "main-arm64",
        "target": "10.16",
        "cflags": "-g -arch arm64",
        "cc": "/usr/bin/clang",
    },
    {
        "name": "main-universal",
        "target": "10.5",
        "cflags": "-isysroot @@XCODE_ROOT@@/SDKs/MacOSX10.5.sdk "
        "-arch i386 -arch ppc -arch ppc64 -arch x86_64",
        "cc": "gcc-4.2",
    },
    {
        "name": "main-ppc64",
        "target": "10.5",
        "cflags": "-isysroot @@XCODE_ROOT@@/SDKs/MacOSX10.5.sdk -arch ppc64",
        "cc": "gcc-4.2",
    },
    {
        "name": "main-x86_64",
        "target": "10.5",
        "cflags": "-arch x86_64 -g",
        "cc": "clang",
    },
    {
        "name": "main-fat3",
        "target": "10.5",
        "cflags": "-isysroot / -arch i386 -arch ppc -arch x86_64",
        "cc": "gcc-4.2",
    },
    {
        "name": "main-intel",
        "target": "10.5",
        "cflags": "-isysroot / -arch i386 -arch x86_64",
        "cc": "clang",
    },
    {
        "name": "main-i386",
        "target": "10.3",
        # 'cflags': '-isysroot @@XCODE_ROOT@@/SDKs/MacOSX10.4u.sdk -arch i386',
        "cflags": "-arch i386 -isysroot /",
        "cc": "clang",
    },
    {
        "name": "main-ppc",
        "target": "10.3",
        "cflags": "-isysroot @@XCODE_ROOT@@/SDKs/MacOSX10.4u.sdk -arch ppc",
        "cc": "gcc-4.0",
    },
    {
        "name": "main-fat",
        "target": "10.3",
        "cflags": "-isysroot @@XCODE_ROOT@@/SDKs/MacOSX10.4u.sdk "
        "-arch i386 -arch ppc",
        "cc": "gcc-4.0",
    },
]


def main(all=False, arch=None):
    basepath = os.path.dirname(__file__)
    builddir = os.path.join(basepath, "prebuilt")
    if not os.path.exists(builddir):
        os.makedirs(builddir)
    src = os.path.join(basepath, "src", "main.m")

    cfg = distutils.sysconfig.get_config_vars()

    BASE_CFLAGS = cfg["CFLAGS"]
    BASE_CFLAGS = BASE_CFLAGS.replace("-dynamic", "")
    BASE_CFLAGS += " -bundle -framework Foundation -framework AppKit"
    while True:
        x = re.sub(r"-arch\s+\S+", "", BASE_CFLAGS)
        if x == BASE_CFLAGS:
            break
        BASE_CFLAGS = x

    while True:
        x = re.sub(r"-isysroot\s+\S+", "", BASE_CFLAGS)
        if x == BASE_CFLAGS:
            break
        BASE_CFLAGS = x

    if arch is None:
        arch = distutils.util.get_platform().split("-")[-1]
        if sys.prefix.startswith("/System") and sys.version_info[:2] == (2, 5):
            arch = "fat"

    name = "main-" + arch
    root = None

    if all:
        for entry in gPreBuildVariants:
            if (not all) and entry["name"] != name:
                continue

            dest = os.path.join(builddir, entry["name"])
            if not os.path.exists(dest) or (
                os.stat(dest).st_mtime < os.stat(src).st_mtime
            ):
                if root is None:
                    fp = os.popen("xcode-select -print-path", "r")
                    root = fp.read().strip()
                    fp.close()

                print("rebuilding %s" % (entry["name"]))

                CC = entry["cc"]
                CFLAGS = (
                    BASE_CFLAGS + " " + entry["cflags"].replace("@@XCODE_ROOT@@", root)
                )
                os.environ["MACOSX_DEPLOYMENT_TARGET"] = entry["target"]
                os.system('"%(CC)s" -o "%(dest)s" "%(src)s" %(CFLAGS)s' % locals())

    dest = os.path.join(builddir, "main-" + arch)

    return dest


if __name__ == "__main__":
    main(all=True)
