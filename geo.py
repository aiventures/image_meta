
from math import pi
from math import sin
from math import sqrt
from math import cos
from math import asin

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
            of two tuples (lat,long) into cartesian  """
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

