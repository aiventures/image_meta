
from math import pi
from math import sin
from math import sqrt
from math import cos
from math import asin
from math import floor
from image_meta.util import Util
from datetime import datetime
import requests

class Geo:
    """ Geo calculations"""

    RADIUS_EARTH = 6371 #Earth Radius in kilometers 

    GEOHACK_URL = "https://geohack.toolforge.org/geohack.php?params="
    NOMINATIM_REVERSE_URL    = "https://nominatim.openstreetmap.org/reverse"
    NOMINATIM_REVERSE_PARAMS = {'format':'geojson','lat':'0','lon':'0',
                                'zoom':'18','addressdetails':'18','accept-language':'de'}

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

    @staticmethod
    def dec2geo(dec):
        """ converts decimals to geo type format"""
        degrees = round(floor(dec),0)
        minutes = round(floor(60*(dec-degrees)),0)
        rest = dec - degrees - ( minutes / 60 )
        seconds = round(rest * 60 * 60)
        return(degrees,minutes,seconds)

    @staticmethod
    def latlon2geohack(latlon):
        """ converts latlon to decimals in geohack format """
        latlon = list(map(lambda n:(round(n,5)),latlon))
        lat,lon = latlon
        lat_ref = "N"
        lon_ref = "E"
        if lat < 0:
            lat_ref = "S"
        if lon < 0:
            lon_ref = "W"
        coord_s = "_".join([str(abs(lat)),lat_ref,str(abs(lon)),lon_ref])
        return coord_s
    
    @staticmethod
    def geohack2dec(geohack:str):
        """ converts geohack string into geo tuple """
        latlon_s = geohack.split("_")
        lat_ref = latlon_s[3]
        lon_ref = latlon_s[7]
        lat_f = 1.0
        lon_f = 1.0
        if lat_ref == "S":
            lat_f = -1.
        if lon_ref == "W":
            lat_f = -1.
        coords_geo = list(map(lambda f:float(f),[*latlon_s[:3],*latlon_s[4:7]]))
        coords = ((lat_f*(coords_geo[0]+(coords_geo[1]/60)+(coords_geo[2]/3600)))
                 ,(lon_f*(coords_geo[3]+(coords_geo[4]/60)+(coords_geo[5]/3600))))
        return coords
    
    @staticmethod 
    def latlon2osm(latlon,detail=18):
        """ converts latlon to osm url """
        # https://www.openstreetmap.org/#map=<detail>/<lat>/<lon>
        detail = str(detail)
        lat = str(latlon[0])
        lon = str(latlon[1])
        return f"https://www.openstreetmap.org/#map={detail}/{lat}/{lon}"

    @staticmethod
    def nominatimreverse2dict(geo_json,debug=False):
        """ transforms json nominatim reverse response into a plain / flattened dictionary format """

        # local method to add dictionary entries
        def add2dict(d:dict,prefix:str):
            if d is None:
                return {}
            keys = []
            trg_dict = {}
            for k,v in d.items():
                key = "_".join([prefix,k])
                keys.append(key)
                trg_dict[key] = v
            trg_dict[("_".join([prefix,"keys"]))] = keys
            return trg_dict

        property_dict = {}  

        # additional parameter from url request
        property_dict["nominatim_url"] = geo_json.get("nominatim_url")
        property_dict["http_status"] = geo_json.get("http_status")
        addressdetails = geo_json.get("addressdetails",18)
        property_dict["addressdetails"] = addressdetails

        err = geo_json.get("error",None)
        if err is not None:
            property_dict["error"] = err
            return property_dict

        # FeatureCollection
        property_dict["osm_type"] = geo_json.get("type")
        # License Notice
        property_dict["osm_licence"] = geo_json.get("licence")

        try:
            features = geo_json.get("features")[0]
        except:
            print("No Features Found in OSM Data")
            features = {}

        # Feature
        property_dict["features_type"] = features.get("type")

        # Properties
        # 'place_id', 'osm_type', 'osm_id', 'place_rank', 'category', 'type', 'importance', 
        # 'addresstype', 'name', 'display_name']
        try:
            properties = features["properties"]
        except:
            print("No Properties Found in OSM Data")
            properties = {}

        for k,v in properties.items():
            if isinstance(v,str):
                property_dict[("properties_"+k)] = v

        properties = {"address":properties.get("address"),
                      "extratag":properties.get("extratags"),
                      "namedetail":properties.get("namedetails")}

        for k,v in properties.items():
                d = add2dict(v,k)
                property_dict.update(d)
            
        # list lat_min lon_min lat_max lat min
        try:
            bbox = list(map(lambda v:float(v),features.get("bbox")))
            bbox = list(map(lambda c:round(c,5),bbox))
            latlon_min = [bbox[1],bbox[0]]
            latlon_max = [bbox[3],bbox[2]]
            property_dict["latlon_min"] = latlon_min 
            property_dict["latlon_max"] = latlon_max
            # calculate distance in m
            property_dict["distance_m"] = round(Geo.get_distance(latlon_min,latlon_max)*1000)
        except:
            property_dict["latlon_min"] = None
            property_dict["latlon_max"] = None

        try:
            geometry = features["geometry"]
            # list lat lon
            latlon = list(map(lambda v:float(v),geometry.get("coordinates")))[::-1]
            latlon = list(map(lambda c:round(c,5),latlon))
            property_dict["latlon"]  = latlon
            latlon = property_dict["latlon"]
            property_dict["url_geohack"] = Geo.GEOHACK_URL+Geo.latlon2geohack(latlon)
            property_dict["url_osm"] = Geo.latlon2osm(latlon,detail=addressdetails)
            # skalar
            property_dict["geometry_type"] = geometry.get("type")
        except:
            print("No Geometry Found in OSM Data")
            property_dict["latlon"] = None
            property_dict["geometry_type"] = None
        
        if debug is True:
            print(f"----Geo Dictionary----")
            for k,v in property_dict.items():
                print(f"\t{k} -> {str(v)} ")
        
        return property_dict
    
    @staticmethod
    def geo_reverse_from_nominatim(latlon,zoom=18,addressdetails=18,debug=False)->dict:
        """ Executes reverse search on nominatim geoserver, returns result als flattened dict 
            specification https://nominatim.org/release-docs/latest/api/Reverse/
            'https://nominatim.openstreetmap.org/reverse?format=geojson&lat=48.7791304&lon=9.186206&zoom=18&addressdetails=18'
        """

        url = Geo.NOMINATIM_REVERSE_URL
        params = Geo.NOMINATIM_REVERSE_PARAMS.copy()
        params["lat"] = str(latlon[0])
        params["lon"] = str(latlon[1])
        params["addressdetails"] = str(addressdetails)
        zoom = str(zoom)
        params["zoom"] = zoom
        response = requests.get(url,params)

        geo_json = response.json()

        geo_json["nominatim_url"] = response.url
        geo_json["http_status"] = response.status_code
        geo_json["addressdetails"] = zoom

        geo_dict = Geo.nominatimreverse2dict(geo_json,debug=debug) 

        return geo_dict