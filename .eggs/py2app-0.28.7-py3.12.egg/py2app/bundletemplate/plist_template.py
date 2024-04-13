import sys

import py2app

__all__ = ["infoPlistDict"]


def infoPlistDict(CFBundleExecutable, plist=None):
    if plist is None:
        plist = {}
    CFBundleExecutable = CFBundleExecutable
    NSPrincipalClass = "".join(CFBundleExecutable.split())
    version = sys.version[:3]
    pdict = {
        "CFBundleDevelopmentRegion": "English",
        "CFBundleDisplayName": plist.get("CFBundleName", CFBundleExecutable),
        "CFBundleExecutable": CFBundleExecutable,
        "CFBundleIconFile": CFBundleExecutable,
        "CFBundleIdentifier": "org.pythonmac.unspecified.%s" % (NSPrincipalClass,),
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": CFBundleExecutable,
        "CFBundlePackageType": "BNDL",
        "CFBundleShortVersionString": plist.get("CFBundleVersion", "0.0"),
        "CFBundleSignature": "????",
        "CFBundleVersion": "0.0",
        "LSHasLocalizedDisplayName": False,
        "NSAppleScriptEnabled": False,
        "NSHumanReadableCopyright": "Copyright not specified",
        "NSMainNibFile": "MainMen",
        "NSPrincipalClass": NSPrincipalClass,
        "PyMainFileNames": ["__boot__"],
        "PyResourcePackages": [
            (s % version)
            for s in [
                "lib/python%s",
                "lib/python%s/lib-dynload",
                "lib/python%s/site-packages.zip",
            ]
        ]
        + ["lib/python%s.zip" % version.replace(".", "")],
        "PyRuntimeLocations": [
            (s % version)
            for s in [
                (
                    "@executable_path/../Frameworks/Python.framework"
                    "/Versions/%s/Python"
                ),
                "~/Library/Frameworks/Python.framework/Versions/%s/Python",
                "/Library/Frameworks/Python.framework/Versions/%s/Python",
                "/Network/Library/Frameworks/Python.framework/Versions/%s/Python",
                "/System/Library/Frameworks/Python.framework/Versions/%s/Python",
            ]
        ],
    }
    pdict.update(plist)
    pythonInfo = pdict.setdefault("PythonInfoDict", {})
    pythonInfo.update(
        {
            "PythonLongVersion": sys.version,
            "PythonShortVersion": sys.version[:3],
            "PythonExecutable": sys.executable,
        }
    )
    py2appInfo = pythonInfo.setdefault("py2app", {})
    py2appInfo.update({"version": py2app.__version__, "template": "bundle"})
    return pdict
