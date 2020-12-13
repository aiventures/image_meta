import json
import glob
import os
from os import listdir
import traceback
from xml.dom import minidom
import pytz
import shutil
import re
import time
import os.path
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

    # file parts
    FILEINFO_FILEPATH = "filepath" 
    FILEINFO_PARTS = "parts"
    FILEINFO_PARENT = "parent"
    FILEINFO_EXISTING_PARENT = "existing_parent"
    FILEINFO_PARENT_IS_DIR = "parent_is_dir"
    FILEINFO_EXISTS = "exists"
    FILEINFO_STEM = "stem"
    FILEINFO_DRIVE = "drive"
    FILEINFO_IS_ABSOLUTE_PATH = "is_absolute_path"
    FILEINFO_SUFFIX = "suffix"
    FILEINFO_IS_DIR = "is_dir"
    FILEINFO_IS_FILE = "is_file"  
    FILEINFO_OBJECT = "object"  
    FILEINFO_ACTIONS = "actions"  
    FILEINFO_CREATED_ON = "created_on"
    FILEINFO_CHANGED_ON = "changed_on"

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
            full_filepath = join_info.get(Persistence.FILEINFO_FILEPATH)
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
            filepath = file_info[Persistence.FILEINFO_FILEPATH]
            file_object = file_info[Persistence.FILEINFO_OBJECT]

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

        fileinfo[Persistence.FILEINFO_FILEPATH] = np
        fileinfo[Persistence.FILEINFO_PARTS] = list(p.parts)
        fileinfo[Persistence.FILEINFO_PARENT] = str(p.parent)
        fileinfo[Persistence.FILEINFO_STEM] = p.stem
        fileinfo[Persistence.FILEINFO_DRIVE] = p.drive
        is_absolute_path = False
        if len(p.drive) > 0:
            is_absolute_path = True
        fileinfo[Persistence.FILEINFO_IS_ABSOLUTE_PATH] = is_absolute_path
        fileinfo[Persistence.FILEINFO_SUFFIX] = p.suffix[1:]
        fileinfo[Persistence.FILEINFO_IS_DIR] = os.path.isdir(p)
        fileinfo[Persistence.FILEINFO_IS_FILE] = os.path.isfile(p)
        parent_is_dir = os.path.isdir(p.parent)

        # only if path contains more than 1 element
        if ( parent_is_dir and len(p.parts) <= 1 ):
            parent_is_dir = False
        fileinfo[Persistence.FILEINFO_PARENT_IS_DIR] = parent_is_dir
        
        # exists
        fileinfo[Persistence.FILEINFO_EXISTS] = False 
        if ( fileinfo[Persistence.FILEINFO_IS_DIR] or  fileinfo[Persistence.FILEINFO_IS_FILE] ):
             fileinfo[Persistence.FILEINFO_EXISTS] = True
        
        # get existing parent if existing
        if parent_is_dir:
            fileinfo[Persistence.FILEINFO_EXISTING_PARENT] = fileinfo[Persistence.FILEINFO_PARENT] 
        else:
            fileinfo[Persistence.FILEINFO_EXISTING_PARENT] = None
        
        fileinfo[Persistence.FILEINFO_OBJECT]  = None
        if fileinfo[Persistence.FILEINFO_IS_DIR]:
            fileinfo[Persistence.FILEINFO_OBJECT]  = Persistence.OBJECT_FOLDER
        
        if fileinfo[Persistence.FILEINFO_IS_FILE]:
            fileinfo[Persistence.FILEINFO_OBJECT]  = Persistence.OBJECT_FILE
            fileinfo[Persistence.FILEINFO_ACTIONS] = Persistence.ACTIONS_FILE
            date_changed = datetime.fromtimestamp(int(os.path.getmtime(fileinfo[Persistence.FILEINFO_FILEPATH])))
            date_created = datetime.fromtimestamp(int(os.path.getctime(fileinfo[Persistence.FILEINFO_FILEPATH])))
            fileinfo[Persistence.FILEINFO_CHANGED_ON] = date_changed
            fileinfo[Persistence.FILEINFO_CREATED_ON] = date_created

        # create potentially new folder name / file name
        if ( fileinfo[Persistence.FILEINFO_EXISTING_PARENT] is not None and fileinfo[Persistence.FILEINFO_OBJECT] is None):
            if fileinfo[Persistence.FILEINFO_SUFFIX] == '':
                fileinfo[Persistence.FILEINFO_OBJECT]  = Persistence.OBJECT_NEW_FOLDER
            else:
                fileinfo[Persistence.FILEINFO_OBJECT]  = Persistence.OBJECT_NEW_FILE
                fileinfo[Persistence.FILEINFO_ACTIONS] = Persistence.ACTIONS_NEW_FILE

        # path is wrong, no actions possible
        if ( not parent_is_dir ) and ( len(p.parts) > 1 ) :
            fileinfo[Persistence.FILEINFO_ACTIONS] = Persistence.MODE_IGNORE

        if showinfo:
            for k,v in fileinfo.items():
                print(f"{k} -> {v}")

        return fileinfo

    @staticmethod
    def delete_related_files(fp,input_file_ext_list=["jpg"],delete_file_ext_list=["arw"],delete=False,verbose=False,show_info=True,case_sensitive=False):
        """ deletes additional files having the same filestem in fileref_list and given file extensions
            or original file extension with appended suffix
            Parameters
            fp: filepath
            case_sensitive: Case Sensitive 
            verbose: show detailed processing information
            show_info: show result list of deleted files
            input_file_ext_list: reference file list (= stem information)
            delete_file_ext_list: file extension list that are to be deleted
            delete: flag to really delete files (otherwise only list is shown)
            
            returns None
        """   

        # initialize file lists
        if not isinstance(input_file_ext_list,list):
            input_file_ext_list = []
        
        if not isinstance(delete_file_ext_list,list):
            delete_file_ext_list = []

        # only delete if all files with deletion extension are found
        delete_only_complete = False

        if not case_sensitive:
            input_file_ext_list = list(map(lambda e:e.lower(),input_file_ext_list))
            delete_file_ext_list = list(map(lambda e:e.lower(),delete_file_ext_list))

        deletion_list = []

        if show_info:
            print(f"Input file extension: {input_file_ext_list} File Deletion extensions {delete_file_ext_list} ")

        for subpath,_,files in os.walk(fp):
            
            if verbose:
                print(f"\n --- Directory {subpath} --- \n{', '.join(files)}")

            file_dict = {}

            for file in files:
                if case_sensitive:
                    file_dict[file] = file
                else:
                    file_dict[file] = file.lower()

            for f_ref,f in file_dict.items():                

                filepath = os.path.join(subpath,f_ref)
                fileinfo = Persistence.get_filepath_info(filepath)
                suffix = fileinfo["suffix"]
                stem = fileinfo["stem"]

                if not case_sensitive:
                    suffix = suffix.lower()
                    stem = stem.lower()
                    
                if not suffix in input_file_ext_list:
                    continue
                
                # regex file stem ending with a deletion file extension
                if len(delete_file_ext_list) > 0:
                    regex = stem+".("+"|".join(delete_file_ext_list)+")$"
                
                    if verbose:
                        print("regex",regex)
                
                    files_found_deletion = [f2 for f2 in file_dict.values() if ( ( len(re.findall(regex, f2)) > 0))]
                    files_found_deletion = [(subpath,f2) for f2 in files_found_deletion]

                    if delete_only_complete and ( not ( len(files_found_deletion) == len(delete_file_ext_list) ) ):
                        continue
                
                    deletion_list.extend(files_found_deletion)

        p_old = None        

        for f_t in deletion_list:
            p = f_t[0]
            f = f_t[1]
            f_ref = os.path.join(p,f)
            
            if not p_old == p:
                p_old = p
                if show_info:
                    print(f"\n--- DELETE FILES: Path {p} ---")
            
            if os.path.isfile(f_ref):
                if delete:
                    try:
                        os.remove(f_ref)
                    except:
                        print(traceback.format_exc())
                        
                if show_info:
                    print(f"    * DELETE {f}")

        return None 

    @staticmethod
    def copy_rename(fp,trg_path_root,regex_filter=None,regex_subst=None,s_subst="",debug=False,save=True):        
        """  Recursively (from subpaths) copies files matching to regex name patterns and/or renames files 
             Parameters
             fp            : source path
             trg_path_root : target path root
             regex_filter  : file filter regex (if set to None, all files will be copied)
             regex_subst   : regex for substitution (if set to None, nothing will be renamed)
             s_subst       : substitution string
             debug         : show debug information
             save          : execute the operations. If false, changes are not saved
             Returns None

            Example regex
            regex_filter = r"url|pdf$" # copies either url or pdf at the end
            regex_subst = "(group)" # all strings "group" will be assignerd match group \1
            s_subst = r"-- this is \1 --" "group" will be replaced by "-- this is group --"
        
        """

        if debug:
            print(f"--- PATH:   {fp} --- \n    TARGET: {trg_path_root}")
            print(f"    FILTER: {regex_filter}")
            print(f"    REPLACE PATTERN: {regex_subst} BY {s_subst}")

        for subpath,_,files in os.walk(fp):

            if debug:
                print(f"\n    --- Processing Folder: {subpath} ---")    
            
            # copy file if possible
            copy_file = True
            add_trg_path = ""
            
            if trg_path_root is not None:        
                # check if we process target paths
                if trg_path_root == os.path.commonpath([subpath,trg_path_root]):            
                    copy_file = False
                    if debug:
                        print(f"              Target Folder, files will not be copied")
                
                # get subdirectory for copy
                add_trg_path = subpath[len(fp)+1:]
                copy_path = os.path.join(trg_path_root,add_trg_path)
                if debug and copy_file:
                    print(f"              Copy Folder: {copy_path}")  
            else:
                copy_file = False
            
            for f in files:
                
                # filter file name
                if regex_filter is not None:
                    regex_search = re.findall(regex_filter,f)
                
                    if len(regex_search) == 0:
                        print(f"        - {f}")    
                        continue
                
                fp_src = os.path.join(subpath,f)
                
                if copy_file:
                    fp_trg = os.path.join(copy_path,f)
                    if debug:
                        print(f"        C {f} copied")  
                    if save:
                        try:
                            shutil.copy2(fp_src, fp_trg)    
                        except IOError:
                            os.makedirs(os.path.dirname(fp_trg),0o777)
                            shutil.copy2(fp_src, fp_trg)  
                else:
                    fp_trg = fp_src
                    
                # now rename file
                if regex_subst is not None:
                    f_subst = re.sub(regex_subst, s_subst, f,flags=re.IGNORECASE)
                    if not f_subst == f:
                        if debug:
                            if not copy_file:
                                print(f"        O    {f} (RENAME)")   
                            print(f"        R -> {f_subst}")      
                            fp_rename = os.path.join(os.path.dirname(fp_trg),f_subst)
                        if save:
                            if os.path.isfile(fp_rename):
                                print(f"        E    {f_subst} exists, no rename")
                            else:    
                                os.rename(fp_trg, fp_rename)      
        return None                