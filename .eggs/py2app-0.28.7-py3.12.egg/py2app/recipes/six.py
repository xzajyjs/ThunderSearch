import sys

SIX_TAB = {
    # six.moves:  (py2, py3)
    "configparser": ("ConfigParser", "configparser"),
    "copyreg": ("copy_reg", "copyreg"),
    "cPickle": ("cPickle", "pickle"),
    "cStringIO": ("cStringIO", "io"),
    "dbm_gnu": ("gdbm", "dbm.gnu"),
    "_dummy_thread": ("dummy_thread", "_dummy_thread"),
    "email_mime_multipart": ("email.MIMEMultipart", "email.mime.multipart"),
    "email_mime_nonmultipart": ("email.MIMENonMultipart", "email.mime.nonmultipart"),
    "email_mime_text": ("email.MIMEText", "email.mime.text"),
    "email_mime_base": ("email.MIMEBase", "email.mime.base"),
    "filter": ("itertools", None),
    "filterfalse": ("itertools", "itertools"),
    "getcwd": ("os", "os"),
    "getcwdb": ("os", "os"),
    "http_cookiejar": ("cookielib", "http.cookiejar"),
    "http_cookies": ("Cookie", "http.cookies"),
    "html_entities": ("htmlentitydefs", "html.entities"),
    "html_parser": ("HTMLParser", "html.parser"),
    "http_client": ("httplib", "http.client"),
    "BaseHTTPServer": ("BaseHTTPServer", "http.server"),
    "CGIHTTPServer": ("CGIHTTPServer", "http.server"),
    "SimpleHTTPServer": ("SimpleHTTPServer", "http.server"),
    "intern": (None, "sys"),
    "map": ("itertools", None),
    "queue": ("Queue", "queue"),
    "reduce": (None, "functools"),
    "reload_module": (None, "importlib"),
    "reprlib": ("repr", "reprlib"),
    "shlex_quote": ("pipes", "shlex"),
    "socketserver": ("SocketServer", "socketserver"),
    "_thread": ("thread", "_thread"),
    "tkinter": ("Tkinter", "tkinter"),
    "tkinter_dialog": ("Dialog", "tkinter.dialog"),
    "tkinter_filedialog": ("FileDialog", "tkinter.FileDialog"),
    "tkinter_scrolledtext": ("ScrolledText", "tkinter.scrolledtext"),
    "tkinter_simpledialog": ("SimpleDialog", "tkinter.simpledialog"),
    "tkinter_ttk": ("ttk", "tkinter.ttk"),
    "tkinter_tix": ("Tix", "tkinter.tix"),
    "tkinter_constants": ("Tkconstants", "tkinter.constants"),
    "tkinter_dnd": ("Tkdnd", "tkinter.dnd"),
    "tkinter_colorchooser": ("tkColorChooser", "tkinter.colorchooser"),
    "tkinter_commondialog": ("tkCommonDialog", "tkinter.commondialog"),
    "tkinter_tkfiledialog": ("tkFileDialog", "tkinter.filedialog"),
    "tkinter_font": ("tkFont", "tkinter.font"),
    "tkinter_messagebox": ("tkMessageBox", "tkinter.messagebox"),
    "tkinter_tksimpledialog": ("tkSimpleDialog", "tkinter.simpledialog"),
    "urllib.robotparser": ("robotparser", "urllib.robotparser"),
    "urllib_robotparser": ("robotparser", "urllib.robotparser"),
    "UserDict": ("UserDict", "collections"),
    "UserList": ("UserList", "collections"),
    "UserString": ("UserString", "collections"),
    "winreg": ("_winreg", "winreg"),
    "xmlrpc_client": ("xmlrpclib", "xmlrpc.client"),
    "xmlrpc_server": ("SimpleXMLRPCServer", "xmlrpc.server"),
    "zip": ("itertools", None),
    "zip_longest": ("itertools", "itertools"),
    "urllib.parse": (("urlparse", "urllib"), "urllib.parse"),
    "urllib.error": (("urllib", "urllib2"), "urllib.error"),
    "urllib.request": (("urllib", "urllib2"), "urllib.request"),
    "urllib.response": ("urllib", "urllib.request"),
}


def check(cmd, mf):
    found = False

    six_moves = ["six.moves"]

    # A number of libraries contain a vendored version
    # of six. Automaticly detect those:
    for nm in mf.graph.node_list():
        if not isinstance(nm, str):
            continue
        if nm.endswith(".six.moves"):
            six_moves.append(nm)

    for mod in six_moves:
        m = mf.findNode(mod)
        if m is None:
            continue

        # Some users of six use:
        #
        #  import six
        #  class foo (six.moves.some_module.SomeClass): pass
        #
        # This does not refer to six.moves submodules
        # in a way that modulegraph will recognize. Therefore
        # unconditionally include everything in the
        # table...

        for submod in SIX_TAB:
            if submod.startswith("tkinter"):
                # Don't autoproces tkinter, that results
                # in significantly larger bundles
                continue

            if sys.version_info[0] == 2:
                alt = SIX_TAB[submod][0]
            else:
                alt = SIX_TAB[submod][1]

            if alt is None:
                continue

            elif not isinstance(alt, tuple):
                alt = (alt,)

            for nm in alt:
                try:
                    mf.import_hook(nm, m)
                    found = True
                except ImportError:
                    pass

        # Look for submodules that aren't automaticly
        # processed.
        for submod in SIX_TAB:
            if not submod.startswith("tkinter"):
                continue

            name = mod + "." + submod
            m = mf.findNode(name)
            if m is not None:
                if sys.version_info[0] == 2:
                    alt = SIX_TAB[submod][0]
                else:
                    alt = SIX_TAB[submod][1]

                if alt is None:
                    continue

                elif not isinstance(alt, tuple):
                    alt = (alt,)

                for nm in alt:
                    mf.import_hook(nm, m)
                    found = True

    if found:
        return {}

    else:
        return None
