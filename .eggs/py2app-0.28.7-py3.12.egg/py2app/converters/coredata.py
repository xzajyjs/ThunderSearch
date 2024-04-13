"""
Automatic compilation of CoreData model files
"""
import os

from py2app.decorators import converts
from py2app.util import mapc, momc


@converts(suffix=".xcdatamodel")
def convert_datamodel(source, destination, dry_run=0):
    destination = os.path.splitext(destination)[0] + ".mom"

    if dry_run:
        return

    momc(source, destination)


@converts(suffix=".xcmappingmodel")
def convert_mappingmodel(source, destination, dry_run=0):
    destination = destination[:-4] + ".cdm"

    if dry_run:
        return

    mapc(source, destination)
