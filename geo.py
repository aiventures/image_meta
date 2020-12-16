from math import pi
from math import sin
from math import sqrt
from math import cos
from math import asin
from math import floor
from image_meta.util import Util
from image_meta.persistence import Persistence
from datetime import datetime
from datetime import timedelta
import requests
import traceback

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

        if not (isinstance(latlon,list) ^ isinstance(latlon,tuple)):
            return geo_dict

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
        
        if isinstance(timestamp,int):
            geo_dict["GPSDateStamp"] = datetime.utcfromtimestamp(timestamp).strftime("%Y:%m:%d")
            geo_dict["GPSTimeStamp"] = datetime.utcfromtimestamp(timestamp).strftime("%H:%M:%S") 

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
        try:
            latlon = list(map(lambda n:(round(n,7)),latlon))
            lat,lon = latlon
        except:
            return None
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
    def latlon_from_osm_url(url:str):
        """ extracts latlon information from an osm link 
            https://www.openstreetmap.org/#map=xx/lat/lon
        """
        url_osm = "https://www.openstreetmap.org/#map="
        latlon = None
        if not(isinstance(url,str) and url.startswith(url_osm) ):
            return None
        
        try:
            #extract latlon info as float number
            latlon = list(map(float,url[len(url_osm):].split("/")[1:]))
            if isinstance(latlon,list) and (len(latlon)!=2):
                latlon = None
        except Exception:
            print(f"--- EXCEPTION latlon_from_osm_url: {url} ---")
            print(traceback.format_exc())    
            return None
        
        return latlon

    @staticmethod 
    def latlon2osm(latlon,detail=18):
        """ converts latlon to osm url """
        # https://www.openstreetmap.org/#map=<detail>/<lat>/<lon>
        if not(isinstance(latlon,list) or isinstance(latlon,tuple)):
            return None

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
    
    @staticmethod
    def get_nearest_gps_waypoint(latlon_ref,gps_fileref,date_s_ref=None,tz = 'Europe/Berlin',dist_max=1000,debug=False)->dict:
        """ Gets closest GPS point in a gps track for given latlon coordinate and time difference if datetime string is given
            latlon_ref  -- latlon coordinates (list or tuple)
            gps_fileref -- filepath to gpsx file
            date_s_ref  -- datetime of reference point  "%m:%d:%Y %H:%M:%S"
            tz          -- timezone (pytz.tzone)
            distmax     -- maximum distance in m whether point will be used as minimum distance (default 1000m)  
            debug       -- outpur additional information
        """

        gps_min = {}

        dist_min = dist_max

        tz = 'Europe/Berlin'
        dt_ref = Util.get_datetime_from_string(datetime_s=date_s_ref,local_tz=tz)
        
        # geohack url
        url_geohack = Geo.GEOHACK_URL+Geo.latlon2geohack(latlon_ref)

        # load gps data 
        gps_coords = Persistence.read_gpx(gpsx_path=gps_fileref)

        if not gps_coords:
            print(f"no gps data found in file {gps_fileref}")
            return gps_min

        num = len(gps_coords.keys())

        timestamps = list(gps_coords.keys())
        timestamps.sort()
        timestamp_min = min(timestamps)
        timestamp_max = max(timestamps)

        # utc from (utc) timestamp 
        dt_min_utc = datetime.utcfromtimestamp(timestamp_min)
        dt_max_utc = datetime.utcfromtimestamp(timestamp_max)

        # get localized datetime
        dt_min = Util.get_localized_datetime(dt_min_utc,tz_in="UTC",tz_out=tz)
        dt_max = Util.get_localized_datetime(dt_max_utc,tz_in="UTC",tz_out=tz)

        # get geo data
        geo_min = gps_coords[timestamp_min]
        latlon_min = (geo_min["lat"],geo_min["lon"])
        geo_max = gps_coords[timestamp_max]
        latlon_max = (geo_max["lat"],geo_max["lon"])

        if debug:
            dist_max = int(1000*Geo.get_distance(latlon_ref,latlon_max))
            dist_min = int(1000*Geo.get_distance(latlon_ref,latlon_min))    
            dist_track = int(1000*Geo.get_distance(latlon_max,latlon_min))    
            print(f"--- Track '{geo_min.get('track_name','Unknown Track')}': {num} data points, duration {dt_max-dt_min}") 
            print(f"    Timezone: {tz}")    
            print(f"    Start latlon: {latlon_min} / Datetime {dt_min}")
            print("                  ",(Geo.GEOHACK_URL+Geo.latlon2geohack(latlon_min))) 
            print(f"    End latlon: {latlon_max} / Datetime {dt_max}")
            print("                ",(Geo.GEOHACK_URL+Geo.latlon2geohack(latlon_max)))     
            print(f"--- Reference latlon: {latlon_ref} / Datetime {dt_ref}")
            print("    Geohack url:",url_geohack)
            print(f"--- Distance: start-ref {dist_min}m, end-ref {dist_max}m, start-end {dist_track}m")
        
        timestamp_min = None

        for timestamp,gps_coord in gps_coords.items():
            latlon = [gps_coord["lat"],gps_coord["lon"]]
            dist = int(1000*Geo.get_distance(latlon_ref,latlon))
            if dist < dist_min:
                dist_min = dist
                datetime_min_utc = datetime.utcfromtimestamp(timestamp)
                datetime_min = Util.get_localized_datetime(datetime_min_utc,tz_in="UTC",tz_out="Europe/Berlin")
                gps_min["timestamp_utc"] = timestamp
                gps_min["datetime"] = datetime_min
                gps_min["lat"] =  gps_coord["lat"]
                gps_min["lon"] =  gps_coord["lon"]
                gps_min["ele"] =  gps_coord["ele"]
                gps_min["distance_m"] = dist_min
                if dt_ref is not None:
                    gps_min["timedelta_from_ref"] =  int(timedelta.total_seconds(datetime_min-dt_ref))
                else:
                    gps_min["timedelta_from_ref"] =  None
                gps_min["url_geohack"] = Geo.GEOHACK_URL+Geo.latlon2geohack(latlon)        

        if gps_min.get("distance_m",dist_max) < dist_max:
            if debug:
                print(f"--- Nearest GPS Trackpoint")
                Util.print_dict_info(d=gps_min)
        else:
            print(f"no gps points found in vicinity of {dist_min} m")        
        
        return gps_min
