#IMAGE_META package

## The IMAGE_META module Elevator Pitch

**_I am a photographer who is tired of maintaining image metadata (EXIF, ITPC, ...) in various tools, especially normal tags and geo coordinates and geo reverse tags like location, city, ... and so on._**

**_This Python module provides a command line level solution to this problem by using exiftool to write data into jpg images._**

## Synopsis

This package provides numerous manipulation features for manipulating jpg Image metadata leveraging the great [EXIF Tool](https://exiftool.org/) and using open street map geo API https://nominatim.org/release-docs/develop/api/Overview/ for getting geo meta data. 

For more Information in IPTC-IIM metadata, check: https://www.iptc.org/std/photometadata/documentation/ 

The package contains the following modules:
* **geo.py** coordinate calculations, access to nominatim API for reverse geo encoding (coordinates to site plain text information),gpx file handling
* **persistence.py** reading + writing plain + json files
* **exif.py** exiftool interface + image metadata handling / transformation 
* **util** datetime calculations, binary search in list, ...
* **controller** bundling logic into helper methods ...

Caveat: Mind the usage terms from Nominatim https://operations.osmfoundation.org/policies/nominatim/ ! So reverse search is only accceptable for a small amount of requests!
