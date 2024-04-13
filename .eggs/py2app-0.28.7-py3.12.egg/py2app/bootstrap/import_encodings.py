def _import_encodings():
    import encodings
    import os
    import pkgutil
    import sys

    del sys.path[:2]
    import encodings.aliases

    encodings.__path__ = pkgutil.extend_path(encodings.__path__, encodings.__name__)

    import encodings.mac_roman

    encodings.aliases.__file__ = os.path.join(
        os.path.dirname(encodings.mac_roman.__file__),
        "aliases.py" + encodings.mac_roman.__file__[:-1],
    )

    if sys.version_info[:2] < (3, 4):
        from imp import reload
    else:
        from importlib import reload

    reload(encodings.aliases)
    reload(encodings)


_import_encodings()
