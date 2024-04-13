import os
import plistlib
import shutil
import sys

from pkg_resources import resource_filename

import py2app.apptemplate
from py2app.util import make_exec, makedirs, mergecopy, mergetree, skipscm


def create_appbundle(
    destdir,
    name,
    extension=".app",
    module=py2app.apptemplate,
    platform="MacOS",
    copy=mergecopy,
    mergetree=mergetree,
    condition=skipscm,
    plist=None,
    arch=None,
    use_old_sdk=False,
    redirect_stdout=False,
):
    if plist is None:
        plist = {}

    kw = module.plist_template.infoPlistDict(
        plist.get("CFBundleExecutable", name), plist
    )
    app = os.path.join(destdir, kw["CFBundleName"] + extension)
    if os.path.exists(app):
        # Remove any existing build artifacts to ensure that
        # we're getting a clean build
        shutil.rmtree(app)
    contents = os.path.join(app, "Contents")
    resources = os.path.join(contents, "Resources")
    platdir = os.path.join(contents, platform)
    dirs = [contents, resources, platdir]
    plist = {}
    plist.update(kw)
    plistPath = os.path.join(contents, "Info.plist")
    if os.path.exists(plistPath):
        with open(plistPath, "rb") as fp:
            if hasattr(plistlib, "load"):
                contents = plistlib.load(fp)
            else:
                # 2.7
                contents = plistlib.readPlist(fp)

            if plist != contents:
                for d in dirs:
                    shutil.rmtree(d, ignore_errors=True)
    for d in dirs:
        makedirs(d)

    with open(plistPath, "wb") as fp:
        if hasattr(plistlib, "dump"):
            plistlib.dump(plist, fp)
        else:
            plistlib.writePlist(plist, fp)

    srcmain = module.setup.main(
        arch=arch, redirect_asl=redirect_stdout, use_old_sdk=use_old_sdk
    )
    if sys.version_info[0] == 2 and isinstance(
        kw["CFBundleExecutable"], unicode  # noqa: F821
    ):
        destmain = os.path.join(platdir, kw["CFBundleExecutable"].encode("utf-8"))
    else:
        destmain = os.path.join(platdir, kw["CFBundleExecutable"])

    with open(os.path.join(contents, "PkgInfo"), "w") as fp:
        fp.write(kw["CFBundlePackageType"] + kw["CFBundleSignature"])

    print("Copy %r -> %r" % (srcmain, destmain))
    copy(srcmain, destmain)
    make_exec(destmain)
    mergetree(
        resource_filename(module.__name__, "lib"),
        resources,
        condition=condition,
        copyfn=copy,
    )
    return app, plist


if __name__ == "__main__":
    create_appbundle("build", sys.argv[1])
