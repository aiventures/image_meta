"""module that allows for manipulate exif / image metdata of image files
   using exiftool. 
   Features_   
   - allows for reverse geo encoding (lookup geo coordinates, procide Geo Names),
     currently uses nominatim / open street map data (caveat: only restricted use allowed!)
   - Use Tag template to write category / image tags into EXIF / IPTC metadata
   - Support of Hierarchical Subject metadata / and import of metadata hierarchy   
"""
import logging
from logging import NullHandler

logger=logging.getLogger(__name__)
logger.addHandler(NullHandler())