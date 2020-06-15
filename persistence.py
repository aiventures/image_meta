import json
import glob
import os
import traceback
from image_meta import util
from xml.dom import minidom
import pytz
from datetime import datetime

class Persistence:
    """ read/write data into persistence (right now, only json)"""
    PATH_SEPARATOR = "\\"

    debug = False

    def __init__(self,path:str,debug=False):
        """ constructor: requires file path where all data are assumed to be found"""
        self.debug = debug
        self.path = path

    def get_file_names(self,file_type="jpg"):
        """ reads all file names for a given file extension (default jpg) """
        files = None
        if os.path.isdir(self.path) is False:
            print(f"[Persistence] {self.path} is not a directory")
        else:
            file_mask = self.path + Persistence.PATH_SEPARATOR + "*." + file_type
            files = glob.glob(file_mask)
        return files

    @staticmethod
    def read_gpx(gpsx_path:str,extension="jpg",debug=False,tz=pytz.timezone("Europe/Berlin")):
        """ reads gpx xml data, returns dict with utc timestamp as key  
            xml data format should be (also supports Track Point Extension
            for GPS smart watch)
            <trk>
                <name>ACTIVE LOG100553</name>
                <trkseg>
                    <trkpt lat="49.123454" lon="8.607288">
                        <ele>30.117</ele>
                        <time>2000-05-19T08:05:53Z</time>
                        <extensions>
                        <ns3:TrackPointExtension>
                            <ns3:hr>140</ns3:hr>
                            <ns3:cad>83</ns3:cad>
                        </ns3:TrackPointExtension>
                        </extensions>                        
                    </trkpt> 
                ...           
        """    
        from xml.dom import minidom
        try:
            gpsx_xml =  minidom.parse(gpsx_path)
        except:
            print(f"Error reading gpsx file {gpsx_path}")
            print(traceback.format_exc())
            return {}

        gps_dict = {}
        gps_pts = 0
        tracks = gpsx_xml.getElementsByTagName('trk')
        for track in tracks:
            track_name =  track.getElementsByTagName("name")[0].firstChild.data
            if debug is True:
                print("TRACK NAME",track_name)
            tracksegs = track.getElementsByTagName('trkseg')
            for trackseg in tracksegs:
                heart_rate = 0
                cadence = 0
                trackpoints = trackseg.getElementsByTagName('trkpt')
                for trackpoint in trackpoints:
                    lat = float(trackpoint.getAttribute('lat'))
                    lon = float(trackpoint.getAttribute('lon'))
                    ele = int(float(trackpoint.getElementsByTagName('ele')[0].firstChild.data))
                    ts_s = trackpoint.getElementsByTagName('time')[0].firstChild.data
                    ts = util.get_timestamp(ts_s)
                    gps_dict[ts] = {"lat":lat, "lon":lon, "ele":ele, "track_name":track_name}
                    gps_pts += 1
                    
                    # optional segments for fitness tracker
                    # <ns3:TrackPointExtension>
                    #    <ns3:hr>140</ns3:hr>  heart rate
                    #    <ns3:cad>83</ns3:cad> cadence / run frequency
                    extension = trackpoint.getElementsByTagNameNS('*','TrackPointExtension')
                    if len(extension) == 1:                        
                        heart_rate =  int(extension[0].getElementsByTagNameNS('*','hr')[0].firstChild.data)
                        cadence = int(extension[0].getElementsByTagNameNS('*','cad')[0].firstChild.data)                  
                    
                if (debug is True):
                    url = r"https://www.openstreetmap.org/#map=16/"+str(lat)+r"/"+str(lon)
                    dt = datetime.utcfromtimestamp(ts).astimezone(tz)
                    print(f"Reading Track {track_name} ... {gps_pts} Points, Date {dt}")
                    if heart_rate > 0:
                        print(f"Running watch: heart rate {heart_rate} cadence {cadence} ")
                    print(f"elevation {ele} last coordinate {url}")

        return gps_dict  

    @staticmethod
    def read_json(filepath:str):   
        """ Reads JSON file"""  
        data = None
        
        if not os.path.isfile(filepath):
            print(f"File path {filepath} does not exist. Exiting...")
            return None
        
        try:
            with open(filepath) as json_file:
                    data = json.load(json_file)                    
        except:
            print(f"Error opening {filepath}")
            print(traceback.format_exc())
            
        return data

    @staticmethod            
    def save_json(filepath,data:dict):     
        """ Saves dictionary data as UTF8 """         
        
        with open(filepath, 'w', encoding='utf-8') as json_file:
            try:
                json.dump(data, json_file, ensure_ascii=False)
            except:
                print(f"Exception writing file {filepath}")
                print(traceback.format_exc())
                
        return None         

    @staticmethod 
    def read_file(filepath,encoding='utf-8'):
        """reads plain file"""
        lines = []
        try:
            with open(filepath,encoding='utf-8') as fp:   
                for line in fp:
                    lines.append(line)
        except:
            print(f"Exception reading file {filepath}")
            print(traceback.format_exc())   
                     
        return lines   


     