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
from configparser import ConfigParser
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
    FILEINFO_URL = "url"
    FILEINFO_SIZE = "size"    

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
            # adding special properties
            # dates and sizes
            date_changed = datetime.fromtimestamp(int(os.path.getmtime(fileinfo[Persistence.FILEINFO_FILEPATH])))
            date_created = datetime.fromtimestamp(int(os.path.getctime(fileinfo[Persistence.FILEINFO_FILEPATH])))
            fileinfo[Persistence.FILEINFO_CHANGED_ON] = date_changed
            fileinfo[Persistence.FILEINFO_CREATED_ON] = date_created
            fileinfo[Persistence.FILEINFO_SIZE] =  Path(filepath).stat().st_size
            # for urls add url field
            if  fileinfo[Persistence.FILEINFO_SUFFIX] == "url":
                fileinfo[Persistence.FILEINFO_URL] = Persistence.read_internet_shortcut(np)

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
    def delete_related_files(fp,src_ext="jpg", del_ext_list=["jpg","xml"],  
                            regex_file_pattern = "^#file#",
                            file_placeholder = "#file#", root_folder_only=True,
                            show_info=True,case_sensitive=False,delete=False):
        """ deletes additional files having the same filestem pattern as files of 
            type src_ext having any extension given in del_ext_list adhering to 
            a given naming pattern regex_file_pattern where filename stems will be 
            represented by file_placeholder. Sounds more complicated than it is,
            try this method. also see example
            
            Parameters
            -------------------
            fp : str
                filepath root
            src_ext : str
                file extension. files with this extension will be used as reference files
            del_ext_list : list (of strings)
                deletion file extension: files having this extension 
                matching in some way to source file will be added for deletion
            regex_file_pattern : str
                regex matching pattern
            file_placeholder : str
                string that should be used as placeholder for filename
            root_folder_only :bool
                delete files only in given file path, not in chidlren folders
            case_sensitive: bool
                Case Sensitive 
            show_info: bool
                show result list of deleted files
            delete: bool
                flag to really delete files (otherwise only list is shown)

            Returns
            ------------
            list
                list of files to be / that were deleted 
                
            Examples
            --------
            folder contains: ['file_a.jpg','file_axx.xml','file_a.tif',,'aa_file_a.xml','b.jpg']
            src_ext='jpg', del_ext_list=['jpg','xml']
            The regex patterns correspond to default values
            regex_file_pattern = ''^#file#'', file_placeholder = '#file#',
            The method will select all jpg file as reference, matching pattern for files to be
            deleted is all files to be deleted (jpg,xml) starting with the same filename stem
            all jpgs (^#file#) will translate to matching pattern:
            ^file_a, matching files for deletion (jpg,xml): file_a.jpg, file_axx.xml
            but not aa_file_a.xml (doesn't start with 'file') or file_a.tif (extension tif)
            ^b.jpg: No matches
                
        """  

        len_ext = -len(src_ext)

        if show_info:
            print(f"delete_similar_files,\n src ext:{src_ext}, trg ext:{del_ext_list},"+
                f" case sensitive:{case_sensitive}, DELETE:{delete}")

        del_files = []    
        for subpath,_,files in os.walk(fp):

            if root_folder_only:
                if not subpath == fp:
                    if show_info:
                        print("Process root only, skip:",subpath)
                    continue

            if show_info:
                print("----------------------")
                print(f"Path {subpath}")

            # get all source files / get all files with deletion extensions
            if case_sensitive:
                re_src =  re.compile((src_ext+"$"))
                del_list = list(filter(lambda f:(f.split(".")[-1] in del_ext_list), files))
            else:
                re_src =  re.compile((src_ext+"$"),re.IGNORECASE)
                del_ext_list = list(map(lambda d_ext:d_ext.lower(),del_ext_list))
                del_list = list(filter(lambda f:(f.split(".")[-1].lower() in del_ext_list)
                                , files))

            src_files = list(filter(lambda f: (re_src.search(f) is not None), files))
            src_files = sorted(src_files,key=str.casefold)
        
            # create search regex for each file 
            for src_file in src_files:
                src_file_stem = src_file[:(len_ext-1)]
                regex_file = regex_file_pattern.replace(file_placeholder,src_file_stem)
                if case_sensitive:
                    regex = re.compile(regex_file)
                else:
                    regex = re.compile(regex_file,re.IGNORECASE)
                
                del_list_files = list(filter(lambda d_ext: (regex.search(d_ext) is not None), del_list))     
                if show_info:
                    print(f"Match Pattern: {regex_file}\n  found {del_list_files}")
                del_list_files = list(map(lambda f:os.path.join(subpath,f), del_list_files))  
                del_files.extend(del_list_files)        

        if show_info:
            print("-------------\nFILE DELETION LIST:")
            
        for del_file in del_files:    
            if show_info:
                print(f"- {del_file}, valid {os.path.isfile(del_file)}",len(del_file))
            if os.path.isfile(del_file):
                if delete:
                    try:
                        os.remove(del_file)
                    except:
                        print(traceback.format_exc())    

        return del_files

    @staticmethod
    def copy_rename(fp,trg_path_root,regex_filter=None,regex_subst=None,s_subst="",debug=False,save=True):        
        """  Recursively (from subpaths) copies files matching to regex name patterns and/or renames files 
            Parameters
            -----------
            fp            : str
            source path
            trg_path_root : target path root
            regex_filter  : file filter regex (if set to None, all files will be copied)
            regex_subst   : regex for substitution (if set to None, nothing will be renamed)
            s_subst       : substitution string
            debug         : show debug information
            save          : execute the operations. If false, changes are not saved
            
            Returns 
            --------------
             None

            Example 
            -----------------
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

    @staticmethod
    def read_internet_shortcut(f,showinfo=False):
        """ reads an Internet shortcut from filepath, returns the url or None 
            if nothing could be found"""
        url = None
        cp = ConfigParser(interpolation=None)
        
        try:
            cp.read(f)
        except Exception as ex:
            print(f"--- EXCEPTION read_internet_shortcut:{ex} ---")
            print(traceback.format_exc())    
            return None
        
        sections = cp.sections()

        for section in sections:
            options = cp.options(section)
            if showinfo:
                print('Section:', section)
                print('- Options:', options)            

            for option in options:
                v = cp.get(section,option)
                if showinfo:
                    print(f" {option} : {v}")
                if (section=="InternetShortcut") and (option=="url"):
                    url = v

        return url  

    @staticmethod
    def copy_meta_files(fp=None,fp_src=None,metadata="metadata.tpl",
                        files_copy=["metadata_exif.tpl","metadata.tpl"],
                        save=True,showinfo=False):
        """ copies files into 1st level folders of a given path
            - will not overwrite existing files
            - additional feature metafile is assumed to be of type json
            containing metadata value DEFAULT_LATLON
            - if weblinks to OSM coordinates are found in the same path,
            DEFAULT_LATLON values will be overwritten in metadta file
            Parameters
            ----------
            fp : str
                root filepath
            fp_src : str
                filepath containing files to copy
            metadata : str
                metadata filename
            files_copy : list
                files to be copies
            save : boolean
                flag if data are to be saved or only simulated
            showinfo : boolean
                flag whether to show processing information
            Returns
            ----------
            boolean: flag whether all was executed
        """
        
        from image_meta.geo import Geo

        # only valid files to copy 
        files_copy = list(filter(lambda f:os.path.isfile(os.path.join(fp_src,f)), files_copy))
        if showinfo:
            print(f"Files from {fp_src} to Copy:\n {files_copy}")
        # root_subdirs = []   
        
        for subpath,subdirs,files in os.walk(fp):
            # only process direct parents
            if subpath == fp:
                if showinfo:
                    print(f"\n*** subpath {subpath} ***\n")

                # root_subdirs = subdirs
                for subdir in subdirs:
                    absolute_path = os.path.join(subpath,subdir)
                    if showinfo:
                        print(f"* subdir {absolute_path}")
                    if ( absolute_path == fp_src ):
                        continue

                    for f in files_copy:
                        # get source file
                        src_fp = os.path.join(fp_src,f)
                        trg_fp = os.path.join(absolute_path,f)
                        if not(os.path.isfile(trg_fp)):
                            if showinfo:
                                print(f"         Copy {f}")
                            if save :
                                shutil.copy(src_fp,trg_fp)
            else:
                # ignore folder with config files
                if subpath == fp_src:
                    continue
                # process subfolder containing metadata and links
                if metadata in files:
                    link_files = list(filter(lambda f:f.endswith("url"),files))
                    if len(link_files) == 0:
                        continue
                    if showinfo:
                        print(f"   --- Subpath {subpath} contains LINKS ---")
                        print(f"   Link files: {link_files}") 
                    latlon = None
                    # check whether any file contains an osm link    
                    for link_file in link_files:
                        link_path = os.path.join(subpath,link_file)
                        if latlon is not None:
                            continue
                        url = Persistence.read_internet_shortcut(link_path)
                        if url is not None:
                            latlon = Geo.latlon_from_osm_url(url)
                            if latlon is not None and showinfo:
                                print(f"   Coordinates found {latlon}")
                    # no coordinates for update
                    if latlon is None:
                        continue
                    # read metadata configuration
                    metadata_fp = os.path.join(subpath,metadata)
                    # config data
                    metadata_dict = Persistence.read_json(metadata_fp)
                    default_latlon = metadata_dict.get("DEFAULT_LATLON",None)
                    if showinfo:
                        print(f"   Change latlon from {default_latlon} to {latlon}")
                    metadata_dict["DEFAULT_LATLON"] = latlon
                    if save:
                        Persistence.save_json(metadata_fp,metadata_dict)
                        if showinfo:
                            print(f"   Update of file {metadata_fp}")
        return True

    @staticmethod
    def get_file_list_mult(fps:list,ignore_paths=[],files_filter=None,
                    delete_marker=None, show_info= False, export_as_path_dir=False):
        """ creates a dictionary of files across file locations
            can be used for identifying duplicates / automatic deletion 

            Parameters
            ----------
            fps : list
                list of filepaths
            ignore_paths : list
                list of strings. when contianed in afile path, these paths will be ignored for processing
            files_filter : list
                only files having a substring contained in the filter list will be processed
            delete_marker : str
                filename. If a directory contains a file with this name, it will be considered to be deleted 
            show_info : bool
                show debugging info 
            export_as_path_dir : bool
                export dictionary will have filename as key (referencing found paths ). 
                If set to true the dictionary key will be path instead
            
            Returns
            -------
            dict: dictionary with detailed information about file duplicate locations, file sizes, dates
            
        """

        if not isinstance(fps,list):
            if isinstance(fps,str) and not os.path.isdir(fps):
                print(f"filelist {fps} is not a list of filepaths")
                return None
            else:
                fps = [fps]

        files_dict = {}
        for fp in fps:
            for subpath,_,files in os.walk(fp):
                # sp = os.path.normpath(os.path.join(fp,subpath))
                # ignore paths
                if Util.contains(subpath,ignore_paths):
                    continue

                # check if subpath contains a marker file for deletion
                cleanup_folder = False
                if isinstance(delete_marker,str):
                    cleanup_folder = os.path.isfile(os.path.join(subpath,delete_marker))
                if os.path.ismount(subpath):
                    cleanup_folder = False

                if cleanup_folder and show_info:
                    print(f"--- FOLDER {subpath} marked for cleanup")

                for f in files:            
                    if isinstance(files_filter,list):
                        if not(Util.contains(f,files_filter)):
                            continue

                    # get absolute path
                    drive,subdrive_path =  os.path.splitdrive(subpath)

                    file_abspath = os.path.join(drive, subdrive_path,f)                                                    

                    file_props = files_dict.get(f,{})
                    file_props_updated = {}

                    # get file path
                    file_paths = file_props.get("path",[])
                    file_paths.append(subpath)
                    file_paths = list(dict.fromkeys(file_paths))
                    file_props_updated["path"] = file_paths
                    file_props_updated["filename"] = f
                    
                    # consider cleanup
                    file_paths_cleanup = file_props.get("cleanup_path",[])
                    if cleanup_folder:
                        file_paths_cleanup.append(subpath)
                    file_paths_cleanup = list(dict.fromkeys(file_paths_cleanup))
                    file_props_updated["cleanup_path"] = file_paths_cleanup

                    # get other attributes
                    size = Path(file_abspath).stat().st_size
                    # byte_info = Util.byte_info(size,num_decimals=1,short=False)
                    created_on = datetime.fromtimestamp(int(Path(file_abspath).stat().st_ctime))
                    changed_on = datetime.fromtimestamp(int(Path(file_abspath).stat().st_mtime))
                    file_props_updated["filesize"] = size
                    file_props_updated["created_on"] = created_on
                    file_props_updated["changed_on"] = changed_on
                    # for urls get link address
                    if f[-3:] == "url":
                        file_props_updated["url"] = Persistence.read_internet_shortcut(file_abspath)

                    # update
                    files_dict.update({f:file_props_updated})
                    if show_info:
                        s_del = ""
                        if cleanup_folder:
                            s_del = " [DELETE]"
                        print("abspath",file_abspath,"subpath",subpath,"drive",drive,"file",f,size,Util.byte_info(size))
                        print(f"[{drive[0]}] {f[:35]}... ({Util.byte_info(size)},created {created_on}) {s_del}")
        
        # export as dictionary with path as key
        if export_as_path_dir:
            path_dict = {}
            for f,v in files_dict.items():
                pl = v["path"]
                for p in pl:
                    file_dict = path_dict.get(p,{})
                    # new dict entry corresponds to file
                    file_dict[f] = v
                    path_dict[p] = file_dict
            files_dict = path_dict

        return files_dict            

    @staticmethod
    def display_file_list_mult(fps,ignore_paths=[],files_filter=None,
                    delete_marker=None, delete_all_duplicates=True,
                    show_del_files_only=False,show_info=False):
        """ display files read across file locations
            can be used for identifying duplicates / automatic deletion 

            Parameters
            ----------
            fps : list
                list of filepaths
            ignore_paths : list
                list of strings. when contianed in afile path, these paths will be ignored for processing
            files_filter : list
                only files having a substring contained in the filter list will be processed
            delete_marker : str
                filename. If a directory contains a file with this name, it will be considered to be deleted 
            delete_all_duplicates : bool
                deletes all file duplicates that are found in search path. Otherwise only file is deleted where
                delete_marker file is located                
            show_del_files_only : bool
                only show files that will be deleted
            show_info : bool
                show debugging info 
            export_as_path_dir : bool
                export dictionary will have filename as key (referencing found paths ). 
                If set to true the dictionary key will be path instead
            
            Returns
            -------
            dict: dictionary with detailed information about file duplicate locations, file sizes, dates
            
        """

        path_dict = Persistence.get_file_list_mult(fps,ignore_paths=ignore_paths,files_filter=files_filter,
                                                   delete_marker=delete_marker, show_info=False,
                                                   export_as_path_dir=True)
            
        path_list = sorted(path_dict.keys(),key=str.lower)

        drive_info_dict = {}
        for p in path_list:
            drive,_ = os.path.splitdrive(p)
            drive_info = drive_info_dict.get(drive,{})
            
            #print(f"---|    + <{p}>")
            print(f"{p}")
            files = sorted(path_dict[p].keys(),key=str.lower)
            file_num = len(files)
            filesize_folder = 0
            contains_delete_file = False
            for f in files:
                file_info = path_dict[p][f]    
                paths = path_dict[p][f]["path"]
                if len(file_info['cleanup_path']) > 0:
                    if ((p in file_info['cleanup_path']) or 
                        delete_all_duplicates):
                        s_cln = "DEL"
                        contains_delete_file = True
                else:
                    s_cln = "---"
                if ((contains_delete_file and show_del_files_only) or
                    (not show_del_files_only)):
                    filesize_folder += file_info['filesize']
                    f_trunc = Util.trunc_string(f,start=33,end=32,s_length=67)
                    print(f"|  +-{s_cln}| {f_trunc}|{file_info['created_on']}|({len(paths)})")
            if filesize_folder > 0:
                print(f"|         FOLDER: {file_num} files, {Util.byte_info(filesize_folder)}")    
                print("|")
            drive_info["size"] = drive_info.get("size",0) + filesize_folder
            drive_info["file_num"] = drive_info.get("file_num",0) + file_num    
            drive_info_dict[drive] = drive_info
        now = datetime.now()
        print(f"\n-- SUMMARY (Date: {now.replace(microsecond=0)})---")
        for d,v in drive_info_dict.items():
            total,used,free = shutil.disk_usage(d)
            free_percent = str(100*free//total)+"%"
            total = Util.byte_info(total)
            used = Util.byte_info(used)
            free = Util.byte_info(free)
            disk_info = f"Used ({used}/{total}), free {free}"
            print(f"Drive {d} {v['file_num']} files, {Util.byte_info(v['size'])}, {disk_info} ({free_percent})")
        
        return path_dict

    @staticmethod
    def display_file_list_by_folder(fps,ignore_paths=[],files_filter=None,
                    delete_marker=None, show_del_files_only=False,show_info=False,
                    show_url=True, start_number=1,show_filename_simple=True,
                    sort_by_date=True,reverse=True):
        """ display files read across file locations and show results by folder

            Parameters
            ----------
            fps : list
                list of filepaths
            ignore_paths : list
                list of strings. when contianed in afile path, these paths will be ignored for processing
            files_filter : list
                only files having a substring contained in the filter list will be processed
            delete_marker : str
                filename. If a directory contains a file with this name, it will be considered to be deleted         
            show_del_files_only : bool
                only show files that will be deleted
            show_info : bool
                show debugging info 
            show_url:
                display url of hyperlink files
            start_number: (int,None)
                numbers files: (None: numbering disabled otherwise the number passed is the start number)
            show_filename_simple: bool
                shows only the filename in the list
            sort_by_date: bool
                sort the result by file change date
            Returns
            -------
            dict: dictionary with detailed information about file duplicate locations, file sizes, dates
            
        """

        # will only be used within this method
        def __fileinfo_as_string__(file_info: dict,show_url=True,number=None,show_filename_simple=False):
            """ transforms file info information for a single file into a display string """
            s_file = Util.trunc_string(file_info['filename'], start=28, end=27, s_length=57)
            changed = file_info['changed_on']
            s_url = ""
            if number is None:
                s_list_char = "-"
            else:
                s_list_char = "("+str(number).zfill(3)+")"
            
            if show_url:
                url = file_info.get("url",None)
                if url is not None:
                    s_url = "\n"+url          
            size = (Util.byte_info(file_info['filesize'], num_decimals=0)).ljust(15)
            if show_filename_simple:
                s = f"{s_list_char} {file_info['filename']}"
            else:
                s = f"{s_list_char} {s_file}|CHG:{changed}|{size}|"
            s += s_url
            return s 

        path_dict = Persistence.get_file_list_mult(fps, ignore_paths=ignore_paths, files_filter=files_filter,
                                                   delete_marker=delete_marker, show_info=show_info,
                                                   export_as_path_dir=True)
        
        paths = sorted(path_dict.keys(),key=str.casefold)

        if isinstance(start_number,int):
            number_idx = start_number
        else:
            number_idx = None

        for p in paths:
            print(f"\n----------------------------\n[FOLDER] {p}")
            path_info = path_dict[p]
            # sort files
            file_info_list = list(path_info.values())
            if sort_by_date:
                file_info_list = sorted(file_info_list,
                                        key=lambda f:f["changed_on"],
                                        reverse=reverse)                
            else: 
                file_info_list = sorted(file_info_list,
                                        key=lambda f:(f["filename"]).lower(),
                                        reverse=reverse)
            num_files = 0
            for file_info in file_info_list:
                num_files += 1
                s_fileinfo = __fileinfo_as_string__(file_info,show_url=show_url,
                                                    number=number_idx,
                                                    show_filename_simple=show_filename_simple)
                if number_idx is not None:
                    number_idx += 1
                print(s_fileinfo)
            print(f"\nFolder ({num_files} files)\n{p}")
            print("----------------------------------------------")
        now = datetime.now()
        print(f"Date: {now.replace(microsecond=0)}, Number of Files:{(number_idx-start_number)}")
                                                   
        return path_dict

    @staticmethod
    def delete_files_mult(fps,ignore_paths=[],files_filter=None,delete_marker=None, 
                        delete_all_duplicates = True, delete_folder=True,
                        delete_ext = ["txt"],persist=False,show_info=True,verbose=False):
        """ looks for a delete marker file, will delete all files of same name and eventually 
            with different extensions and optionally all its duplicates

            Parameters
            ----------
            fps : list
                list of filepaths
            ignore_paths : list
                list of strings. when contianed in a file path, these paths will be ignored for processing
            files_filter : list
                only files having a substring contained in the filter list will be processed
            delete_marker : str
                filename. If a directory contains a file with this name, it will be considered to be deleted 
            delete_all_duplicates : bool
                deletes all file duplicates tjhat are found in search path. Otherwise only file is deleted where
                delete_marker file is located
            delete_folder : bool
                after deletion of files folder is deleted as well (only if it is empty)
            delete_ext : list
                list of extensions of files that should vbe deleted
            persist : bool
                save deletions (oherwise only results of analysis are shown)
            show_info : bool
                show debugging info
            verbose : bool
                show detailed information
            
            Returns
            -------
            tuple: (folder_list, file_list) files and folders that were deleted                         
        """

        fl = Persistence.get_file_list_mult(fps,ignore_paths=ignore_paths,files_filter=files_filter,
                            delete_marker=delete_marker, show_info=False)

        if show_info:
            if isinstance(fl,dict):
                num_files = len(list(fl.keys()))
            print("----------")
            print(f"Delete extensions {delete_ext}, Duplicates:{delete_all_duplicates}, Folders:{delete_folder}, File count:{num_files}")
            print("----------")

        delete_files = []       
        delete_folders = [] 
            
        for f,v in fl.items():

            cleanup_paths = v["cleanup_path"]
            p_list = v["path"] 
            if len(cleanup_paths) == 0:
                continue
                
            f_info = Persistence.get_filepath_info(f)
            f_stem = f_info["stem"]
            f_del_list = []
            for ext in delete_ext:
                f_del_list.append(f"{f_stem}.{ext}")
            
            # add delete marker
            f_del_list.append(delete_marker)
            if show_info and verbose:    
                print("----")
                print(f"DELETE: file {f} \n        Paths {p_list}")
                print(f"        Del paths {cleanup_paths})")        
                
            # process all file duplicates
            for p in p_list: 
                if ((not (p in cleanup_paths)) and (not delete_all_duplicates)):
                    continue
                if show_info and verbose:
                    print(f"        * DELETE DIRECTORY: {p}")
                for f_del in f_del_list:
                    f_del_abspath = os.path.join(p,f_del)
                    if (not os.path.isfile(f_del_abspath)):
                        continue
                    delete_folders.append(p)
                    if show_info and verbose:
                        print(f"          - {f_del[:40]}...{f_del[-6:]}")
                    delete_files.append(f_del_abspath)

        delete_files = sorted(list(dict.fromkeys(delete_files)),key=str.lower)
        
        del_fp_dict = {}
        for del_fp in delete_files:
            _,del_p = os.path.splitdrive(del_fp)
            del_fp_list = del_fp_dict.get(del_p,[])
            del_fp_list.append(del_fp)
            del_fp_dict[del_p] = del_fp_list
        
        delete_files = []
        file_refs = sorted(del_fp_dict.keys())
        for file_ref in file_refs:
            delete_files.extend(del_fp_dict[file_ref])
        
        delete_folders = sorted(list(dict.fromkeys(delete_folders)),key=str.lower)

        if show_info:
            print(f"\n--- FILES FOR DELETION (SAVED: {persist}) ---")
        
        for del_file in delete_files:
            try:
                if show_info:
                    print(f"- DELETE {del_file[:50]}...{del_file[-15:]}")            
                if persist:
                    os.remove(del_file)         
            except IOError as ex:
                print (f"Error: {ex.filename} - {ex.strerror}")
                print(traceback.format_exc())           

        if show_info:
            print(f"\n--- FOLDERS FOR DELETION (SAVED: {persist}) ---")
        for del_folder in delete_folders:
            try:
                if show_info:
                    print(f"- DELETE {del_folder}")            
                if persist:
                    os.rmdir(del_folder)          
            except IOError as ex:
                print (f"Error: {ex.filename} - {ex.strerror}")
                print(traceback.format_exc())           
        
        return (delete_folders,delete_files)

    @staticmethod
    def get_file_groups(fp:str="",regex_list:list=["^(.{1,19})"],
                        file_match_type:str="ANY", single_match:bool=True,
                        show_info:bool=False):
        """ reads all files in a given filepath fp and will return
            groups of files in a dict that belong together, according 
            to a list of regex expressions given as r. The Group name is the found regex expression
            file_match_type (ALL or ANY) will determine whether all expressions need to match or 
            if any of the regex matches is sufficient
            if single_match is True, the file matching a pattern will only be listed once, 
            for the first regex pattern found
            Example 
            fp = "C.\\ ..."
            regex = ["^(.{1,19})"]
            will return groups for files thsat start with the same 19 characters of filename        
        """

        # get all files first
        filelist = Persistence.get_file_list_mult([fp])
        filegroup_dict = {}
        
        if file_match_type != "ALL":
            file_match_type = "ANY"

        if show_info:
            print("\n --- get_file_groups (Persistence) ---")
            print(f"    FILE MATCH TYPE: [{file_match_type}] FILE REGEX RULES: {regex_list} \n") 
        
        for f in filelist.keys():
            if show_info:
                print(f"FILE: {f}")
            
            # check for all regexex
            file_regex_match_list = []
            regex_match_result_list = []
            m_result = ""
            for r in regex_list:            
                m = re.match(r,f)
                m_result = ""
                if m:
                    file_regex_match_list.append(True)
                    # add result as key
                    regex_match_result_list.append(m.groups()[0])
                    m_result += (m.groups()[0]+", ")
                else:
                    file_regex_match_list.append(False)
                    m_result += "None, "
            
            # check for results     
            file_match_result = False    
            if file_match_type == "ALL":
                file_match_result = all(file_regex_match_list)
            else:
                file_match_result = any(file_regex_match_list)
            
            if show_info:
                print(f"  FILE {f}, match: {file_match_result} ({m_result})")
                
            
            # add match results as file patterns
            if file_match_result:
                for regex_match_result in regex_match_result_list:
                    fg_list = filegroup_dict.get(regex_match_result,[])
                    paths = filelist[f]["path"]
                    for p in paths:
                        fp = os.path.join(p,f)
                        fg_list.append(fp)
                    filegroup_dict[regex_match_result] = fg_list
                    if single_match:
                        break
                    
        return filegroup_dict

    def analyze_file_groups(filegroups:dict,regex_list:list=[],
                            file_match_type:str="ANY",filegroup_match_type:str="ANY",
                            show_info:bool=False):
        """ 
            gets filegroups (as retrieved from method get file groups)
            analyses whether each files does match to all/any regex rules 
            supplied in a list. 
            Also returns matching result whether
            any / all files in a file group did match
            file_match_type can be ALL / ANY (all/any regex rules need to match on file level)
            filegroup_match_type ALL / ANY: is returning true if all / any file_match_type rule
            checks did return true within a filegroup. If regex list is empty True is returned by
            default
        """

        if file_match_type != "ALL":
            file_match_type = "ANY"

        if filegroup_match_type != "ALL":
            filegroup_match_type = "ANY"    
        
        if show_info:
            print("\n--- analyze_file_groups (Persistence) ---")                  
            print(f"    FILEGROUP MATCH TYPE: {filegroup_match_type}")
            print(f"    FILE MATCH TYPE: [{file_match_type}] FILE REGEX RULES: {regex_list} \n")

        match_result_dict = {}
        filegroup_list_dict = {}

        for fg,filelist in filegroups.items():

            n_files = len(filelist)
            if show_info:
                print(f"FILEGROUP: {fg}, num files: {n_files}")
            filegroup_match_result = False
            filegroup_match_list = []

            file_list_dict = {}
            filegroup_result_dict = {}

            for f in filelist:        
                #file_match_list = []
                #file_match_result = False        

                # list of regex matches per file
                file_regex_match_list = []                
                m_result = ""
                for r in regex_list:            
                    m = re.match(r,f)
                    m_result = ""
                    if m:
                        file_regex_match_list.append(True)
                        m_result += (m.groups()[0]+", ")
                    else:
                        file_regex_match_list.append(False)
                        m_result += "None, "

                file_match_result = False

                if file_match_type == "ALL":
                    file_match_result = all(file_regex_match_list)
                else:
                    file_match_result = any(file_regex_match_list)
                
                # special case: empty regex list defaults to true
                if not regex_list:
                    file_match_result = True
                
                if show_info:
                    print(f"  FILE {f}, match: {file_match_result} ({m_result})")

                filegroup_match_list.append(file_match_result)
                file_list_dict[f] = file_match_result 

            # get match result on filegroup level
            if filegroup_match_type == "ALL":
                filegroup_match_result = all(filegroup_match_list)
            else:
                filegroup_match_result = any(filegroup_match_list)
                
            # special case: Empty Regex List always defaults to True
            if not regex_list:
                filegroup_match_result = True
            
            if show_info:
                print(f"  FILEGROUP MATCH [{filegroup_match_type}]: {filegroup_match_result}")

            filegroup_result_dict["filegroup_match"] = filegroup_match_result
            filegroup_result_dict["file_match_dict"] = file_list_dict
            filegroup_result_dict["num_files"] = n_files

            filegroup_list_dict[fg] = filegroup_result_dict

        return filegroup_list_dict

    def group_and_analyze_files( fp:str="",file_group_regex_list:list=[],
                                 file_group_match_type:str="ANY",file_regex_list:list=[] ,
                                 file_match_type:str="ANY",file_group_match_type_analyze:str="ANY",
                                 file_group_single_match:bool=True,show_info:bool=False):
        """ for a given file path, with a list of regexes bundle files
            into groups. Within these groups you can further analyze
            whether any or all files within a group meet some criteria
            defined by another regex list. Can be useful to identify duplicates
            , files belonging to a workflow, files with a similar name and operate on them
            (for example deleting them)
            Parameters
            - fp: file path
            - file_group_regex_list: regex for getting groups for files belonging together
            - file_group_match_type: (ALL/ANY) either all or any regexes so that file name matches pattern
            - file_regex_list: regex to filter files in resulting file groups ".*(dng)$"
            - file_match_type: file check to fit regexes given in file_regex_list (ALL/ANY)
            - file_group_match_type_analyze: files in a file group need to match (ALL/ANY)
            - file_group_single_match: Only add a file match when a file matches to criteria for first occurence
                                    Avoids double listing of file paths in result list                        
            - show_info: display info
        """
            
        # get file groups
        fg = Persistence.get_file_groups(fp,file_group_regex_list,file_match_type=file_group_match_type,
                            single_match=file_group_single_match,show_info=show_info)


        # do the file analysis based on file name
        fa = Persistence.analyze_file_groups(fg,file_regex_list,file_match_type=file_match_type,
                                    filegroup_match_type=file_group_match_type_analyze,
                                    show_info=show_info)        
        
        return fa        