def _site_packages():
    import os
    import site
    import sys

    paths = []
    prefixes = [sys.prefix]
    if sys.exec_prefix != sys.prefix:
        prefixes.append(sys.exec_prefix)
    for prefix in prefixes:
        paths.append(
            os.path.join(
                prefix, "lib", "python%d.%d" % (sys.version_info[:2]), "site-packages"
            )
        )

    if os.path.join(".framework", "") in os.path.join(sys.prefix, ""):
        home = os.environ.get("HOME")
        if home:
            # Sierra and later
            paths.append(
                os.path.join(
                    home,
                    "Library",
                    "Python",
                    "%d.%d" % (sys.version_info[:2]),
                    "lib",
                    "python",
                    "site-packages",
                )
            )

            # Before Sierra
            paths.append(
                os.path.join(
                    home,
                    "Library",
                    "Python",
                    "%d.%d" % (sys.version_info[:2]),
                    "site-packages",
                )
            )

    # Work around for a misfeature in setuptools: easy_install.pth places
    # site-packages way to early on sys.path and that breaks py2app bundles.
    # NOTE: this is hacks into an undocumented feature of setuptools and
    # might stop to work without warning.
    sys.__egginsert = len(sys.path)

    for path in paths:
        site.addsitedir(path)


_site_packages()
