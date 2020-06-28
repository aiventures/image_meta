import json
import glob
import os
from os import listdir
import traceback
from xml.dom import minidom
import pytz
import shutil
from datetime import datetime

from image_meta import util
from image_meta.util import Util

class Persistence:
    """ read/write data into persistence (right now, only json)"""
    PATH_SEPARATOR = os.sep

    debug = False

    def __init__(self,path:str,debug=False):
        """ constructor: requires file path where all data are assumed to be found"""
        self.debug = debug
        self.path = os.path.normpath(path)

    def get_file_names(self,file_type="jp*"):
        """ reads all file names for a given file extension (default jpg) """
       
        files = None
        if os.path.isdir(self.path) is False:
            print(f"[Persistence] {self.path} is not a directory")
        else:
            file_mask = self.path + Persistence.PATH_SEPARATOR + "*." + file_type
            files = glob.glob(file_mask)
        
        files = list(map(os.path.normpath,files))
        return files

    @staticmethod
    def read_gpx(gpsx_path:str,debug=False,tz=pytz.timezone("Europe/Berlin")):
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
                    ts = Util.get_timestamp(ts_s)
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
                        gps_dict[ts]["heart_rate"] = heart_rate  
                        gps_dict[ts]["cadence"] = cadence       
                    
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
            with open(filepath,encoding=encoding) as fp:   
                for line in fp:
                    lines.append(line)
        except:
            print(f"Exception reading file {filepath}")
            print(traceback.format_exc())   
                     
        return lines   

    @staticmethod
    def create_filename(filename,path=None,file_extension=None,append_timestamp=False):
        """ helper method to create a filename based on name, path , file extension and option
            to append a timestamp """

        if append_timestamp is True:              
            timestamp = "_"+datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            timestamp = ""    

        if file_extension is None:
            file_end = ""
        else:
            file_end = "." + file_extension
        
        if path is None:
            path_save = ""
        else:
            path_save = path + Persistence.PATH_SEPARATOR

        return path_save+filename+timestamp+file_end

    @staticmethod
    def save_file(data,filename,path=None,file_extension=None,append_timestamp=False,append_data=False,encoding='utf-8'):
        """ saves data as string to file, optional with appended timestamp, returns path  
            if file already exists and append is set to true, data will be appended
        """

        if not ( path is None ) :
            if not ( os.path.isdir(path) ):
                print(f"{path} is not a valid directory")
                return None 

        file_path = Persistence.create_filename(filename,path=path,file_extension=file_extension,append_timestamp=append_timestamp)
        s = ""

        if ( append_data is True ) and ( os.path.isfile(file_path) ):
            data_file = ''.join(Persistence.read_file(file_path))
            data = data_file + data

        with open(file_path, 'w', encoding=encoding) as f:
            try:
                f.write(data)
                s = "Data saved to " + file_path
            except:
                print(f"Exception writing file {filename}")
                print(traceback.format_exc())     
                s = "No data was saved" 
                
        return s        
    
    @staticmethod
    def copy_files(src_path,trg_path,ext=""):
        """copies files from one file path to another
           filter ext can be supplied to only copy certain file types
           returns list of copied files in target directory"""
        
        file_list = listdir(src_path)
        copied_files = [shutil.copy(os.path.join(src_path,f),os.path.join(trg_path,f)) 
                        for f in file_list if f.endswith(ext)]
        return copied_files


     