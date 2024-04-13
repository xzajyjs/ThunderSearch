def _update_path():
    import os
    import sys

    resources = os.environ["RESOURCEPATH"]
    sys.path.append(
        os.path.join(
            resources, "lib", "python%d.%d" % (sys.version_info[:2]), "lib-dynload"
        )
    )
    sys.path.append(
        os.path.join(resources, "lib", "python%d.%d" % (sys.version_info[:2]))
    )
    sys.path.append(
        os.path.join(
            resources,
            "lib",
            "python%d.%d" % (sys.version_info[:2]),
            "site-packages.zip",
        )
    )


_update_path()
