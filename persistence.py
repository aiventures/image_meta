import json
import glob
import os
from os import listdir
import traceback
from xml.dom import minidom
import pytz
import shutil
import re
from xml.dom import minidom
from datetime import datetime
from pathlib import Path
from image_meta import util
from image_meta.util import Util

class Persistence:
    """ read/write data into persistence (right now, only json)"""
    
    PATH_SEPARATOR = os.sep
    OBJECT_FOLDER = "folder"
    OBJECT_FILE = "file"
    OBJECT_NEW_FOLDER = "new_folder"
    OBJECT_NEW_FILE = "new_file"    

    # file operations
    MODE_IGNORE = "0"
    MODE_CREATE = "C"
    MODE_READ   =  "R"
    MODE_UPDATE = "U"    
    MODE_DELETE = "D"
    MODE_CREATE_UPDATE = "X"
    MODE_TXT = { "0":"MODE IGNORE", "R":"MODE READ","U":"MODE UPDATE","C":"MODE CREATE","D":"MODE DELETE","X":"MODE CREATE UPDATE"}
    # allowed file actions
    ACTIONS_NEW_FILE = "XC"
    ACTIONS_FILE = "XRUD"
    ACTIONS_CHANGE_FILE = "XUDC"

    # regex pattern for a raw file name: 3 letters 5 decimals
    REGEX_RAW_FILE_NAME = r"[a-zA-Z]{3}\d{5}"

    debug = False

    def __init__(self,path:str,debug=False):
        """ constructor: requires file path where all data are assumed to be found"""
        self.debug = debug
        self.path = os.path.normpath(path)

    def get_file_names(self,file_type="jp*g"):
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
    def get_file_list(path,file_type_filter=None):
        """ returns list of files for given file type (or file type list) 
            path can be a file name, a file path, or a list 
            of files, paths. File type none selects all files
        """

        # process input path can be a single file a list or a path, 
        # transform raw information into list of files
        img_list_raw = []
        img_list = []

        if isinstance(path,list):
            img_list_raw = path
        elif isinstance(path,str):
            img_list_raw = [path]
        else:
            print(f"{path} no valid path")
            return None
        
        for path_ref in img_list_raw:
            if os.path.isdir(path_ref):
                images = Persistence(path_ref).get_file_names(file_type="*")
            elif os.path.isfile(path_ref):
                images = [os.path.normpath(path_ref)]
            else:
                continue
            img_list.extend(images)
         
        # filter items by extension
        if not file_type_filter is None:
            file_types = []
            if isinstance(file_type_filter,str):
                file_types = [file_type_filter]
            elif isinstance(file_type_filter,list):
                file_types = file_type_filter
            file_types = list(map(lambda f: ("."+f.lower()), file_types))
            img_list = list(filter(lambda p:Path(p).suffix.lower() in file_types,img_list))

        return img_list

    @staticmethod
    def read_gpx(gpsx_path:str,debug=False,tz=pytz.timezone("Europe/Berlin"))->dict:
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
                    ele = float(float(trackpoint.getElementsByTagName('ele')[0].firstChild.data))
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
                        try:  
                            heart_rate =  int(extension[0].getElementsByTagNameNS('*','hr')[0].firstChild.data)
                        except:
                            heart_rate = 0
                        try:
                            cadence = int(extension[0].getElementsByTagNameNS('*','cad')[0].firstChild.data)     
                        except:
                            cadence = 0
                        gps_dict[ts]["heart_rate"] = heart_rate  
                        gps_dict[ts]["cadence"] = cadence       
                    
                if (debug is True):
                    url = r"https://www.openstreetmap.org/#map=16/"+str(lat)+r"/"+str(lon)
                    dt = pytz.utc.localize(datetime.utcfromtimestamp(ts)).astimezone(tz)
                    print(f"Reading Track {track_name} ... {gps_pts} Points, Last Date {dt}")
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
            with open(filepath,encoding='utf-8') as json_file:
                    data = json.load(json_file)                    
        except:
            print(f"**** Error opening {filepath} ****")
            print(traceback.format_exc())
            print("***************")
            
        return data

    @staticmethod            
    def save_json(filepath,data:dict):     
        """ Saves dictionary data as UTF8 """         
        
        with open(filepath, 'w', encoding='utf-8') as json_file:
            try:
                json.dump(data, json_file, indent=4,ensure_ascii=False)
            except:
                print(f"Exception writing file {filepath}")
                print(traceback.format_exc())
                
        return None         

    @staticmethod 
    def read_file(filepath,encoding='utf-8',show=False):
        """reads plain file, if show is set it will be displayed"""
        lines = []
        try:
            with open(filepath,encoding=encoding) as fp:   
                for line in fp:
                    lines.append(line)
        except:
            print(f"Exception reading file {filepath}")
            print(traceback.format_exc())   
        
        if show is True:
            for line in lines:
                print(line.strip())
                     
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
    def replace_file_suffix(filepath:str,suffix:str):
        """replaces file suffix"""
        p = Path(filepath)
        old_suffix = "".join(p.suffixes)
        l = len(old_suffix)
        return os.path.normpath(str(p)[:-l]+"."+suffix)

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
    def filter_files(path,ext=None):
        """ filters out files from a given directory
            ext is a string or a list of extension to be filtered
            returns list of full path file names
        """

        if ext is not None:
            if isinstance(ext,str):
                ext_filter = [ext]
            elif isinstance(ext,list):
                ext_filter = ext
            ext_filter = list(map(lambda s:("."+s.lower()),ext_filter))
        else:
            ext_filter = None
        
        file_list = listdir(path)
        
        # filter extensions
        if ext_filter is None:
            copy_list = file_list
        else:
            copy_list = list([f for f in file_list if Path(f).suffix.lower() in ext_filter ])
            # special case: no suffix
            if ("" in ext):
                copy_list_empty = list([f for f in file_list if Path(f).suffix == ""])
                copy_list.extend(copy_list_empty)

        # only copy files
        copy_list = list(filter(lambda f:os.path.isfile(os.path.join(path,f)),copy_list))        

        return copy_list

    @staticmethod
    def copy_files(src_path,trg_path,ext=None):
        """copies files from one file path to another
           filter ext can be supplied to only copy certain file types
           returns list of copied files in target directory"""
        
        copy_list = Persistence.filter_files(path=src_path,ext=ext)

        copied_files = [shutil.copy(os.path.join(src_path,f),os.path.join(trg_path,f)) 
                        for f in copy_list]

        return copied_files
    
    @staticmethod
    def rename_raw_img_files(path,ext=None,debug=False,simulate=False):
        """ renames raw image files (3 letters 5 decimals) by replacing the 3 letters by folder name"""
        regex = re.compile(Persistence.REGEX_RAW_FILE_NAME, re.IGNORECASE)
        p = Path(path)

        try:
            parent_dir = (Path(path).parts[-1])
        except:
            parent_dir = ""
        if debug is True:
            print(f"Parent Directory {parent_dir}")
        file_list = Persistence.filter_files(path,ext) 
        for src_file_name in file_list:
            r = re.search(regex,src_file_name)
            if r is not None:
                trg_file_name = regex.sub("".join([parent_dir,"_",r.group()[3:]]),src_file_name)
                src = os.path.join(p,src_file_name)
                trg = os.path.join(p,trg_file_name)
                if debug is True:

                    print(f"rename {src_file_name} -> {trg_file_name}" )

                if os.path.isfile(trg):
                    print(f"Rename {src_file_name}: File {trg} already exists and can't be renamed!")
                else:
                    if simulate is False:
                        os.rename(src,trg)
            else:
                if debug is True:
                    print(f"File {src_file_name} will be ignored (doesn't match {regex})")
    
    @staticmethod
    def get_file_full_path(filepath:str="",filename:str="",check=True,allow_new=True,showinfo=False
                          ,object_filter=[OBJECT_NEW_FILE,OBJECT_FILE]):
        """ checks for existence whether filename or combination of path and filename points to an existing file
            if check flag is set, otherwise it will return just a path 
            if allow_new is set, it will check whether a combination of path / file will lead to a valid file path
            object_filter allows for returning only certain object types (folder/files, existing/new)
            """

        full_filepath = None

        # check if path or file name alone are already file names
        file_info_list = []

        if (filepath != "" and filename != ""):
            join_path = str(Path(os.path.normpath(os.path.join(filepath,filename))))
            join_info =  Persistence.get_filepath_info(join_path)
            full_filepath = join_info.get("filepath")
            file_info_list.append(join_info)
        
        if filepath != "":
            path_info = Persistence.get_filepath_info(filepath)
            file_info_list.append(path_info)

        if filename != "":
            file_info = Persistence.get_filepath_info(filename)
            file_info_list.append(file_info)

        if not check:
            # check for plausible results
            return full_filepath
        
        full_filepath = None

        # check if path or file name alone are already file name
        for file_info in file_info_list:
            filepath = file_info["filepath"]
            file_object = file_info["object"]

            if file_object in object_filter:
                full_filepath = filepath

            if showinfo:
                print(f"Checking Filepath {filepath} returns type {file_object}")

        return full_filepath
    
    @staticmethod    
    def get_filepath_info(filepath,showinfo=False):
        """ returns metainfo for a given file path 
            Notabene: doesn't fully work in Desktop folders in Windows (folder info wrong) """
        fileinfo = {}
        try:
            np = os.path.normpath(filepath)
            p = Path(np)
        except:
            np = str(f"ERROR in filepath {filepath}")
            p = Path("")

        fileinfo["filepath"] = np
        fileinfo["parts"] = list(p.parts)
        fileinfo["parent"] = str(p.parent)
        fileinfo["stem"] = p.stem
        fileinfo["drive"] = p.drive
        is_absolute_path = False
        if len(p.drive) > 0:
            is_absolute_path = True
        fileinfo["is_absolute_path"] = is_absolute_path
        fileinfo["suffix"] = p.suffix[1:]
        fileinfo["is_dir"] = os.path.isdir(p)
        fileinfo["is_file"] = os.path.isfile(p)
        parent_is_dir = os.path.isdir(p.parent)

        # only if path contains more than 1 element
        if ( parent_is_dir and len(p.parts) <= 1 ):
            parent_is_dir = False
        fileinfo["parent_is_dir"] = parent_is_dir
        
        # exists
        fileinfo["exists"] = False 
        if ( fileinfo["is_dir"] or  fileinfo["is_file"] ):
             fileinfo["exists"] = True
        
        # get existing parent if existing
        if parent_is_dir:
            fileinfo["existing_parent"] = fileinfo["parent"] 
        else:
            fileinfo["existing_parent"] = None
        
        fileinfo["object"]  = None
        if fileinfo["is_dir"]:
            fileinfo["object"]  = Persistence.OBJECT_FOLDER
        
        if fileinfo["is_file"]:
            fileinfo["object"]  = Persistence.OBJECT_FILE
            fileinfo["actions"] = Persistence.ACTIONS_FILE

        # create potentially new folder name / file name
        if ( fileinfo["existing_parent"] is not None and fileinfo["object"] is None):
            if fileinfo["suffix"] == '':
                fileinfo["object"]  = Persistence.OBJECT_NEW_FOLDER
            else:
                fileinfo["object"]  = Persistence.OBJECT_NEW_FILE
                fileinfo["actions"] = Persistence.ACTIONS_NEW_FILE

        # path is wrong, no actions possible
        if ( not parent_is_dir ) and ( len(p.parts) > 1 ) :
            fileinfo["actions"] = Persistence.MODE_IGNORE

        if showinfo:
            for k,v in fileinfo.items():
                print(f"{k} -> {v}")

        return fileinfo
            
