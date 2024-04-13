AUTO_PACKAGES = [
    # Embbedded datafiles accessed using
    # ``__file__`` relative paths.
    "botocore",
    "docutils",
    "pylint",
    # Import dependencies between C extensions
    "h5py",
    # pycyptodome contains C libraries
    # that are loaded using ctypes and are
    # not detected by the regular machinery.
    # Just bail out and include this package
    # completely and in the filesystem.
    "Crypto",
    # Swig using packages
    "sentencepiece",
    # Uses pkg_resources to load resources,
    # and that doesn't work when the package
    # is a zipfile...
    "imageio_ffmpeg",
    # Various
    "numpy",
    "scipy",
    "tensorflow",
]


def check(cmd, mf):
    to_include = []
    for python_package in AUTO_PACKAGES:
        m = mf.findNode(python_package)
        if m is None or m.filename is None:
            continue

        to_include.append(python_package)

    if to_include:
        return {"packages": to_include}
    return None
