def converts(suffix):
    """
    Use the following convention when writing a file converter::

        from py2app.decorators import converts

        @converts(suffix=".png")
        def convert_png(source_file, destination_file):
            pass
    """

    def wrapper(func):
        func.py2app_suffix = suffix
        return func

    return wrapper
