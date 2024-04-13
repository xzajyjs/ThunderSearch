"""
Automatic compilation of XIB files
"""
from __future__ import print_function

import os
import subprocess

from py2app.decorators import converts
from py2app.util import check_output, reset_blocking_status

gTool = None


def _get_ibtool():
    global gTool
    if gTool is None:
        if os.path.exists("/usr/bin/xcrun"):
            try:
                gTool = check_output(["/usr/bin/xcrun", "-find", "ibtool"])[:-1]
            except subprocess.CalledProcessError:
                raise IOError("Tool 'ibtool' not found")
        else:
            gTool = "ibtool"

    return gTool


@converts(suffix=".xib")
def convert_xib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"

    print("compile %s -> %s" % (source, destination))
    if dry_run:
        return

    with reset_blocking_status():
        subprocess.check_call([_get_ibtool(), "--compile", destination, source])


@converts(suffix=".nib")
def convert_nib(source, destination, dry_run=0):
    destination = destination[:-4] + ".nib"
    print("compile %s -> %s" % (source, destination))

    if dry_run:
        return

    with reset_blocking_status():
        subprocess.check_call([_get_ibtool, "--compile", destination, source])
