""" module to handle overall execution of EXIF handling """

from image_meta.persistence import Persistence
from image_meta.util import Util
from image_meta.geo import Geo
from image_meta.exif import ExifTool

class Controller(object):
    nop = ""
