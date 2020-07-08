
from math import pi
from math import sin
from math import sqrt
from math import cos
from math import asin
from image_meta.util import Util
from datetime import datetime

class Geo:
    RADIUS_EARTH = 6371 
    """ Earth Radius in kilometers """

    @staticmethod
    def latlon2cartesian(lat_lon,radius=RADIUS_EARTH):
        """"transforms (lat,lon) to cartesian coordinates (x,y,z) """
        lat_deg,lon_deg = lat_lon
        lat = (pi/180)*lat_deg
        lon = (pi/180)*lon_deg
        lat_radius = cos(lat)*radius
        x = sin(lon)*lat_radius
        y = cos(lon)*lat_radius
        z = sin(lat)*radius
        return (x,y,z)
    
    @staticmethod
    def get_distance(latlon1,latlon2,radius=RADIUS_EARTH,debug=False,cartesian_length=False):
        """ calculates distance (wither cartesian (default) or arc segment length) 
            of two tuples (lat,long) into cartesian in kilometers  """
        c1 = Geo.latlon2cartesian(latlon1)
        c2 = Geo.latlon2cartesian(latlon2)
        delta_c = [coord[1]-coord[0] for coord in list(zip(c2,c1))]
        # distance and arc segment
        distance = sqrt(sum([delta**2 for delta in list(delta_c)]))
        if cartesian_length is False:
            distance_arc = 2*radius*asin((distance/2)/radius)
            if debug is True:
                print("Arc Distance:",distance_arc,"Distance:",distance," Difference:",(distance_arc-distance))
            distance = distance_arc
        if debug is True:
            print("Delta Coordinates (X,Y,Z):",delta_c,"\n Distance:",distance)              
        return distance  
    
    @staticmethod
    def get_exifmeta_from_latlon(latlon,altitude=None,timestamp:int=None):
        """Creates Exif Metadata Dictionary for GPS Coordinates"""
        geo_dict={}

        lat,lon = latlon

        print("xxx",lat,lon)
        latref = "N"
        lonref = "E"

        if lat < 0:
            latref = "S"
        if lon < 0:
            lonref = "W"
        
        geo_dict["GPSLatitude"] = lat
        geo_dict["GPSLatitudeRef"] = latref
        geo_dict["GPSLongitude"] = lon
        geo_dict["GPSLongitudeRef"] = lonref
               
        if altitude is not None:
            geo_dict["GPSAltitudeRef"] = "above"
            geo_dict["GPSAltitude"] = round(altitude,0)
        
        if timestamp is not None:
            geo_dict["GPSDateStamp"] = datetime.fromtimestamp(timestamp).strftime("%Y:%m:%d")
            geo_dict["GPSTimeStamp"] = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S") 

        return geo_dict 

