IMAGE_META package
This package provides numerous manipulation features for manipulating jpg Image metadata leveraging the great [EXIF Tool](https://exiftool.org/) and using open street map geo API https://nominatim.org/release-docs/develop/api/Overview/ for getting geo meta data. 
The package contains the following modules:

* **geo.py** coordinate calculations, access to nominatim API for reverse geo encoding (coordinates to site plain text information),gpx file handling
* **persistence.py** reading + writing plain + json files
* **exif.py** exiftool interface + image metadata handling / transformation 
* **util** datetime calculations, binary search in list, ...

Caveat: Mind the usage terms from Nominatim https://operations.osmfoundation.org/policies/nominatim/ ! So reverse search is only accceptable for a small amount of requests!