import os
import sys

from modulegraph.util import imp_find_module

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    set
except NameError:
    from sets import Set as set

try:
    basestring
except NameError:
    basestring = str


def check(cmd, mf):
    m = mf.findNode("Image") or mf.findNode("PIL.Image")
    if m is None or m.filename is None:
        return None

    have_PIL = bool(mf.findNode("PIL.Image"))

    plugins = set()
    visited = set()

    # Most users should now use Pillow, which always uses
    # "PIL.Image", which can simply the code below.
    for folder in sys.path:
        if not isinstance(folder, basestring):
            continue

        for extra in ("", "PIL"):
            folder = os.path.realpath(os.path.join(folder, extra))
            if (not os.path.isdir(folder)) or (folder in visited):
                continue
            for fn in os.listdir(folder):
                if not fn.endswith("ImagePlugin.py"):
                    continue

                mod, ext = os.path.splitext(fn)
                try:
                    sys.path.insert(0, folder)
                    imp_find_module(mod)
                    del sys.path[0]
                except ImportError:
                    pass
                else:
                    plugins.add(mod)
        visited.add(folder)
    s = StringIO("_recipes_pil_prescript(%r)\n" % list(plugins))
    print(plugins)
    plugins = set()
    # sys.exit(1)
    for plugin in plugins:
        if have_PIL:
            mf.implyNodeReference(m, "PIL." + plugin)
        else:
            mf.implyNodeReference(m, plugin)

    mf.removeReference(m, "FixTk")
    # Since Imaging-1.1.5, SpiderImagePlugin imports ImageTk conditionally.
    # This is not ever used unless the user is explicitly using Tk elsewhere.
    sip = mf.findNode("SpiderImagePlugin")
    if sip is not None:
        mf.removeReference(sip, "ImageTk")

    # The ImageQt plugin should only be usefull when using PyQt, which
    # would then be explicitly imported.
    # Note: this code doesn't have the right side-effect at the moment
    # due to the way the PyQt5 recipe is structured.
    sip = mf.findNode("PIL.ImageQt")
    if sip is not None:
        mf.removeReference(sip, "PyQt5")
        mf.removeReference(sip, "PyQt5.QtGui")
        mf.removeReference(sip, "PyQt5.QtCore")

        mf.removeReference(sip, "PyQt4")
        mf.removeReference(sip, "PyQt4.QtGui")
        mf.removeReference(sip, "PyQt4.QtCore")
        pass

    imagefilter = mf.findNode("PIL.ImageFilter")
    if imagefilter is not None:
        # Optional dependency on numpy to process
        # numpy data passed into the filter. Remove
        # this reference to ensure numpy is only copied
        # when it is actually used in the application.
        mf.removeReference(imagefilter, "numpy")

    image = mf.findNode("PIL.Image")
    if image is not None:
        # Optional dependency on numpy to convert
        # to a numpy array.
        mf.removeReference(image, "numpy")

    return {
        "prescripts": ["py2app.recipes.PIL.prescript", s],
        "include": "PIL.JpegPresets",  # import from PIL.JpegPlugin in Pillow 2.0
        "flatpackages": [os.path.dirname(m.filename)],
    }
