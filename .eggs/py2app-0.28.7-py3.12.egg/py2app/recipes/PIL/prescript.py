def _recipes_pil_prescript(plugins):
    try:
        import Image

        have_PIL = False
    except ImportError:
        from PIL import Image

        have_PIL = True

    import sys

    def init():
        if Image._initialized >= 2:
            return

        if have_PIL:
            try:
                import PIL.JpegPresets

                sys.modules["JpegPresets"] = PIL.JpegPresets
            except ImportError:
                pass

        for plugin in plugins:
            try:
                if have_PIL:
                    try:
                        # First try absolute import through PIL (for
                        # Pillow support) only then try relative imports
                        m = __import__("PIL." + plugin, globals(), locals(), [])
                        m = getattr(m, plugin)
                        sys.modules[plugin] = m
                        continue
                    except ImportError:
                        pass

                __import__(plugin, globals(), locals(), [])
            except ImportError:
                print("Image: failed to import")

        if Image.OPEN or Image.SAVE:
            Image._initialized = 2
            return 1

    Image.init = init
