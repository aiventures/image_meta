""" module to handle overall execution of EXIF handling """

import os
import pytz
import time
import traceback
from image_meta.persistence import Persistence
from image_meta.util import Util
from image_meta.geo import Geo
from image_meta.exif import ExifTool
from pathlib import Path
from datetime import datetime

class Controller(object):

        # checks which items have existing file references
        # get exiftool availability 
        # get additional keyword file
        # get hierarchical keywords
        # calibration image file and date, calculate offset
        # get gpx file
        # read default latlon file
        # create default lat lon file id not present and mode will create it

    # input parameters for exif
    TEMPLATE_WORK_DIR = "WORK_DIR"
    TEMPLATE_IMG_EXTENSIONS = "IMG_EXTENSIONS"
    TEMPLATE_EXIFTOOL = "EXIFTOOL"
    TEMPLATE_META = "META"
    TEMPLATE_OVERWRITE_KEYWORD = "OVERWRITE_KEYWORD"
    TEMPLATE_OVERWRITE_META = "OVERWRITE_META"
    TEMPLATE_KEYWORD_HIER = "KEYWORD_HIER"
    TEMPLATE_TECH_KEYWORDS = "TECH_KEYWORDS"

    # Other Metadata Fields
    TEMPLATE_COPYRIGHT = "COPYRIGHT"
    TEMPLATE_COPYRIGHT_NOTICE = "COPYRIGHT_NOTICE"
    TEMPLATE_CREDIT = "CREDIT"
    TEMPLATE_SOURCE = "SOURCE"
    TEMPLATE_TRANSMISSION = "TRANSMISSION"
    TEMPLATE_BYLINE = "BYLINE"
    TEMPLATE_BYLINE_TITLE = "BYLINE_TITLE"
    TEMPLATE_WRITER_EDITOR = "WRITER_EDITOR"
    TEMPLATE_CAPTION_WRITER = "CAPTION_WRITER"
    TEMPLATE_AUTHORS_POSITION = "AUTHORS_POSITION"
    TEMPLATE_USER_COMMENT = "USER_COMMENT"
    TEMPLATE_INTELLECTUAL_GENRE = "INTELLECTUAL_GENRE"
    TEMPLATE_WEB_STATEMENT = "WEB_STATEMENT"
    TEMPLATE_USAGE_TERMS = "USAGE_TERMS"
    TEMPLATE_URL = "URL"                
    
    # Geocoordinate Handling
    TEMPLATE_TIMEZONE = "TIMEZONE"
    TEMPLATE_CREATE_GEO_METADATA = "CREATE_GEO_METADATA"
    TEMPLATE_CALIB_IMG = "CALIB_IMG"
    TEMPLATE_CALIB_DATETIME = "CALIB_DATETIME"
    TEMPLATE_CALIB_OFFSET = "CALIB_OFFSET"
    TEMPLATE_GPX = "GPX"
    TEMPLATE_GPX_FILE = "GPX_FILE"
    TEMPLATE_GPX_FILE = "GPX_FILE_ACTIONS"
    TEMPLATE_DEFAULT_LATLON = "DEFAULT_LATLON"
    TEMPLATE_DEFAULT_LATLON_FILE = "DEFAULT_LATLON_FILE"
    TEMPLATE_DEFAULT_LATLON_FILE_ACTIONS = "DEFAULT_LATLON_FILE_ACTIONS"
    TEMPLATE_CREATE_LATLON = "CREATE_LATLON"    
    TEMPLATE_CREATE_DEFAULT_LATLON = "CREATE_DEFAULT_LATLON"  
    TEMPLATE_DEFAULT_MAP_DETAIL = "DEFAULT_MAP_DETAIL"
    TEMPLATE_DEFAULT_REVERSE_GEO = "DEFAULT_REVERSE_GEO"
    TEMPLATE_DEFAULT_META_EXT = "DEFAULT_META_EXT"   
    TEMPLATE_DEFAULT_GPS_EXT = "DEFAULT_GPS_EXT"   
    TEMPLATE_GPS_READ_REMOTE = "GPS_READ_REMOTE"   

    TEMPLATE_PARAMS = [TEMPLATE_WORK_DIR,TEMPLATE_IMG_EXTENSIONS,TEMPLATE_EXIFTOOL, TEMPLATE_META, TEMPLATE_OVERWRITE_KEYWORD, 
                       TEMPLATE_OVERWRITE_META, TEMPLATE_KEYWORD_HIER, TEMPLATE_TECH_KEYWORDS, TEMPLATE_COPYRIGHT, 
                       TEMPLATE_COPYRIGHT_NOTICE, TEMPLATE_CREDIT, TEMPLATE_SOURCE, TEMPLATE_TRANSMISSION,
                       TEMPLATE_BYLINE,TEMPLATE_BYLINE_TITLE,TEMPLATE_WRITER_EDITOR,TEMPLATE_CAPTION_WRITER,TEMPLATE_AUTHORS_POSITION,
                       TEMPLATE_USER_COMMENT, TEMPLATE_INTELLECTUAL_GENRE,TEMPLATE_WEB_STATEMENT,TEMPLATE_USAGE_TERMS,TEMPLATE_URL,                         
                       TEMPLATE_TIMEZONE,TEMPLATE_CREATE_GEO_METADATA,
                       TEMPLATE_CALIB_IMG, TEMPLATE_CALIB_DATETIME,TEMPLATE_CALIB_OFFSET,TEMPLATE_GPX, 
                       TEMPLATE_DEFAULT_LATLON,TEMPLATE_CREATE_LATLON,
                       TEMPLATE_CREATE_DEFAULT_LATLON,TEMPLATE_DEFAULT_MAP_DETAIL,
                       TEMPLATE_DEFAULT_REVERSE_GEO,TEMPLATE_DEFAULT_GPS_EXT,TEMPLATE_DEFAULT_META_EXT,TEMPLATE_GPS_READ_REMOTE]
    
    # mapping template values to meta data
    TEMPLATE_META_MAP = {}

    # template default mapping values
    TEMPLATE_DEFAULT_VALUES = { TEMPLATE_IMG_EXTENSIONS:["jpg","jpeg"],
                                TEMPLATE_TIMEZONE:"Europe/Berlin",
                                TEMPLATE_OVERWRITE_KEYWORD:False,
                                TEMPLATE_OVERWRITE_META:False,
                                TEMPLATE_TECH_KEYWORDS:True,
                                TEMPLATE_COPYRIGHT:"Unknown Artist",
                                TEMPLATE_COPYRIGHT_NOTICE:"All rights reserved",
                                TEMPLATE_CREDIT:"Unknown Artist",
                                TEMPLATE_SOURCE:"Own Photography",
                                TEMPLATE_TRANSMISSION:"ImageMeta (Python)",
                                TEMPLATE_BYLINE:"Unknown Artist",
                                TEMPLATE_BYLINE_TITLE:"Honorable",
                                TEMPLATE_WRITER_EDITOR:"Unknown Editor",
                                TEMPLATE_CAPTION_WRITER:"Unknown Caption Writer",
                                TEMPLATE_AUTHORS_POSITION:"Photographer",
                                TEMPLATE_USER_COMMENT:"", 
                                TEMPLATE_INTELLECTUAL_GENRE:"Landscape",
                                TEMPLATE_WEB_STATEMENT:"https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode",
                                TEMPLATE_USAGE_TERMS:"All rights reserved",
                                TEMPLATE_URL:"",                                       
                                TEMPLATE_CREATE_DEFAULT_LATLON:True,
                                TEMPLATE_DEFAULT_MAP_DETAIL:17,
                                TEMPLATE_KEYWORD_HIER:{},
                                TEMPLATE_CALIB_OFFSET:0,
                                TEMPLATE_DEFAULT_GPS_EXT:"geo",
                                TEMPLATE_DEFAULT_META_EXT:"meta",
                                TEMPLATE_CREATE_GEO_METADATA:True }                                

    @staticmethod
    def create_param_template(filepath="",name="",showinfo=True):
        """ Creates a parameter template that can be used for filling out necessary references for tagging jpg data
            simply replace all data in json beginning with underscore _ additional text as help is (INFO...) provided
            showinfo parameter will also store additional information on parameters
        """
        tpl_dict = {}
        
        #check if filepath is a valid directory
        fp = Persistence.get_file_full_path(filepath=filepath,filename=name)

        if fp is None:
            print(f"path {filepath} and file {name} are not valid")       
            return None
        
        # General Infos
        tpl_dict["INFO_1"] = "template; Enter null w/o double quotes if you do not need respective parameter"    
        tpl_dict["INFO_2"] = "If no paths for file references are supplied work directory will be used to find data"    
        tpl_dict["INFO_3"] = "USe double back slash '\\' or single slash '/' as path separators  ! " 
        
        # Reference to Exif Tool / TEMPLATE_EXIF
        tpl_dict["INFO_EXIFTOOL_FILE"] = "INFO: Enter full path to your EXIFTOOL.EXE executable"
        tpl_dict["EXIFTOOL_FILE"] ="exiftool.exe"

        # Work Directory / TEMPLATE_WORK_DIR
        tpl_dict["INFO_WORK_DIR"] = "INFO: Work Directory, If supplied only file names need to be supplied"
        tpl_dict["WORK_DIR"] = "_workdir_"
        tpl_dict["INFO_IMG_EXTENSIONS"] = "INFO: Supported Image File Extensions"
        tpl_dict["IMG_EXTENSIONS"] = ("jpg","jpeg")
        
        # Keywords / KEYWORD KEYWORD_HIER
        tpl_dict["INFO_KEYWORD_HIER_FILE"] = "INFO: UTF8 Text file containing your metadata keyword hierarchy"
        tpl_dict["KEYWORD_HIER_FILE"] = "_keyword_hier_file_"
        tpl_dict["INFO_TECH_KEYWORDS"] = "INFO: Generate keywords with camera detail settings"
        tpl_dict["TECH_KEYWORDS"] = True
        tpl_dict["INFO_META_FILE"] = "INFO: UTF8 Text file with additonal meta data, each entry line needs to be in args format, eg '-keywords=...'"
        tpl_dict["META_FILE"] = "_meta_file_"
        tpl_dict["INFO_OVERWRITE_KEYWORD"] = "INFO: Overwrite Keywords / Hier Subject or append from meta file "
        tpl_dict["OVERWRITE_KEYWORD"] = False
        tpl_dict["INFO_OVERWRITE_META"] = "INFO: Overwrite with Metadata from metadata template file"
        tpl_dict["OVERWRITE_META"] = True

        # Copyright Info
        tpl_dict["INFO_COPYRIGHT"] = "INFO:Copyright" 
        tpl_dict["COPYRIGHT"] = "AUTHOR" 
        tpl_dict["INFO_COPYRIGHT_NOTICE"] = "INFO:Image copyright Notice" 
        tpl_dict["COPYRIGHT_NOTICE"] = "(C) 2020 AUTHOR All Rights Reserved" 
        tpl_dict["INFO_CREDIT"] = "INFO:Image Credit"
        tpl_dict["CREDIT"] = "AUTHOR"  
        tpl_dict["INFO_SOURCE"] = "INFO:Image Source"
        tpl_dict["SOURCE"] = "AUTHOR"  
        
        # Geo Coordinate Handling / 
        tpl_dict["INFO_CREATE_GEO_METADATA"] = "INFO: Create Geo Metadata"
        tpl_dict["CREATE_GEO_METADATA"] = True
        tpl_dict["INFO_CALIB_IMG_FILE"] = "INFO: image displaying time of your GPS "
        tpl_dict["CALIB_IMG_FILE"] = "gps.jpg"
        tpl_dict["INFO_CALIB_DATETIME"] = "INFO: Enter Date Time displayed by your GPS image in Format with Quotes 'YYYY:MM:DD HH:MM:SS' "
        tpl_dict["CALIB_DATETIME"] = datetime.now().strftime("%Y:%m:%d %H:%M:%S")     
        
        tpl_dict["INFO_CALIB_OFFSET"]  = "INFO: Date Time Offset (instead of using calibration image and datetime info)"
        tpl_dict["INFO_CALIB_OFFSET2"] = "      DATETIME_OFFSET = GPS_DATETIME - CAMERA_DATETIME"
        tpl_dict["INFO_CALIB_OFFSET3"] = "      Image datetime and gps datetime will be ignored if this value is <> 0"
        tpl_dict["CALIB_OFFSET"] = 0   

        tpl_dict["INFO_TIMEZONE"] = "INFO: Enter Time Zone (values as defined by pytz), default is 'Europe/Berlin'"
        tpl_dict["TIMEZONE"] = "Europe/Berlin"
        tpl_dict["INFO_GPX_FILE"] = "INFO: Filepath to your gpx file from your gps device"
        tpl_dict["GPX_FILE"] = "geo.gpx"       
        tpl_dict["INFO_DEFAULT_LATLON"] = "DEFAULT LAT LON COORDINATES if Geocoordinates or GPX Data can't be found"
        tpl_dict["DEFAULT_LATLON"] = (49.01304,8.40433)  
        tpl_dict["INFO_CREATE_LATLON"] = "Create LATLON FILE, values (0:ignore, C:create, R:read , U:update)"
        tpl_dict["CREATE_LATLON"] = Persistence.MODE_CREATE     
        tpl_dict["INFO_CREATE_DEFAULT_LATLON"] = "Create Default LATLON FILE, values (0:ignore, C:create, R:read , U:update)"
        tpl_dict["CREATE_DEFAULT_LATLON"] = Persistence.MODE_CREATE            
        tpl_dict["INFO_DEFAULT_LATLON_FILE"] = "DEFAULT LAT LON FILE PATH for Default Geocoordinates if they can't be found for single image"
        tpl_dict["DEFAULT_LATLON_FILE"] = "default.geo"          
        tpl_dict["INFO_DEFAULT_MAP_DETAIL"] = "DEFAULT Detail level for map links (1...18)"
        tpl_dict["DEFAULT_MAP_DETAIL"] = 18     
        tpl_dict["INFO_DEFAULT_GPS_EXT"] = "DEFAULT GPS File Extension"
        tpl_dict["DEFAULT_GPS_EXT"] = "geo"   
        tpl_dict["INFO_GPS_READ_REMOTE"] = "Read Remote Service Data"
        tpl_dict["GPS_READ_REMOTE"] = True                     

        if not showinfo:
            keys = list(tpl_dict.keys())
            for k in keys:
                if k[:5] == "INFO_":
                    tpl_dict.pop(k)

        Persistence.save_json(filepath=fp,data=tpl_dict)
        return fp
    
    @staticmethod
    def read_params_from_file(filepath=None,showinfo=True):
        """ reads control parameters from file and returns them
            as dictionary """

        IGNORE = ["WORK_DIR","TIMEZONE","CREATE_DEFAULT_LATLON"]

        """ reads control parameters from file """
        control_params = {}
        
        if not os.path.isfile(filepath):            
            print(f"Read Params: Param File {filepath} is not a file. Image files can not be processed")
            return control_params
        
        params_raw = Persistence.read_json(filepath)

        work_dir = params_raw.get("WORK_DIR")
        if work_dir is not None:
            if not os.path.isdir(work_dir):
                print(f"Read Params: Work Dir {work_dir} is not a valid path, check config file {filepath}")
                work_dir = ""
        
        control_params["WORK_DIR"] = work_dir
        
        timezone = params_raw.get("TIMEZONE","Europe/Berlin")
        control_params["TIMEZONE"] = timezone

        create_default_latlon = params_raw.get("CREATE_DEFAULT_LATLON",Persistence.MODE_READ)
        control_params["CREATE_DEFAULT_LATLON"] = create_default_latlon
        control_params["CREATE_DEFAULT_LATLON_TEXT"] = Persistence.MODE_TXT.get(create_default_latlon,"NA")

        if showinfo is True:
            print(f"WORKING DIRECTORY -> {work_dir}")
            print(f"TIME ZONE -> {timezone}")
            print(f"CREATE LATLON DEFAULT FILE -> {create_default_latlon} ({Persistence.MODE_TXT[create_default_latlon]})")

        for k,v in params_raw.items():

            K = k.upper()
            
            if ( "INFO_" in k ) or ( k.upper() in IGNORE ):
                continue 
            
            if showinfo:
                print(f"PARAMETER {K} -> {v}")
            
            # convert datetime fields / currently not used
            if "DATETIME" in K:
                #dt_loc = Util.get_datetime_from_string(datetime_s=v,local_tz=timezone,debug=showinfo)
                control_params[K] = v
                continue
            
            if k == "DEFAULT_LATLON":
                try:
                    latlon = [float(v[0]),float(v[1])]
                except:
                    latlon = None
                control_params[K] = latlon
                continue

            #convert to full path
            if "FILE" in K:
                
                object_filter = [Persistence.OBJECT_FILE,Persistence.OBJECT_NEW_FILE]
                full_path = Persistence.get_file_full_path(filepath=work_dir,filename=v,object_filter=object_filter,showinfo=False) 
                if full_path is None:
                    print(f"Couldn't get a path for filepath {work_dir} and filename {v} ")
                    continue

                file_actions = Persistence.get_filepath_info(full_path)["actions"]
                control_params[K] = full_path
                control_params[(K+"_ACTIONS")] = file_actions
                    
                continue

            #read other control parameters
            control_params[k] = v

        return control_params

    @staticmethod
    def retrieve_nominatim_reverse(filepath=None,latlon=None,save=False,zoom=17,remote=False,debug=False)->dict:
        """ retrieves reverse geodata from a file, or from nominatim reverse service
            if file doesn't exist. Save will retrieve existing geodata.
            remote forces remote retrieve 
            Optional only data from file will be read if latlon is set to initial
        """
        geo_dict = {}

        if filepath is None:
            file_exists = False
        else:
            file_exists = os.path.isfile(filepath)

        if ( file_exists and (remote is False)):
            try:
                if debug is True:
                    print(f"reading geodata from {filepath}")
                geo_dict = Persistence.read_json(filepath)
            except:
                geo_dict = {}
        
        # read from nominatim reverse search
        if ((not geo_dict) and ( latlon is not None )): 
            if debug is True:
                print(f"reading reverse geo data for latlon {latlon}")
            time.sleep(1) # graceful access to remote location
            geo_dict = Geo.geo_reverse_from_nominatim(latlon,zoom=zoom,debug=debug)

        if ((save is True) and (filepath is not None) and (file_exists is False)):
            try:
                Persistence.save_json(filepath=filepath,data=geo_dict)
                if (debug is True):
                    print(f"Saving data to {filepath}")
            except:
                print(f"Error writing data to file {filepath}")
        
        return geo_dict

    @staticmethod
    def prepare_execution(template_dict:dict,showinfo=False):
        """ validates template and checks, which actions can be done (reading hierarchy,geodata, exiftool,...) """
        
        input_dict = {}

        def is_file(param):
            p = param + "_FILE_ACTIONS"
            return ( template_dict.get(p) == Persistence.ACTIONS_FILE )    

        # get exiftool availability
        if is_file(Controller.TEMPLATE_EXIFTOOL):            
            input_dict[Controller.TEMPLATE_EXIFTOOL] = template_dict[(Controller.TEMPLATE_EXIFTOOL+"_FILE")]
            exiftool_ref = input_dict[Controller.TEMPLATE_EXIFTOOL]
        else:
            print("No Exiftool, preparation will be aborted")
            return

        # check working directory
        work_dir = template_dict.get(Controller.TEMPLATE_WORK_DIR,"")
        if work_dir == "":
            print(f"{work_dir} is not a valid working directory check template")
            return

        input_dict[Controller.TEMPLATE_WORK_DIR] = work_dir

        # allowed image file extensions
        input_dict[Controller.TEMPLATE_IMG_EXTENSIONS] = template_dict.get(Controller.TEMPLATE_IMG_EXTENSIONS,["jpg"])

        # read keyword hierarchy
        keyword_hier = {}

        if is_file(Controller.TEMPLATE_KEYWORD_HIER):
            f = template_dict[(Controller.TEMPLATE_KEYWORD_HIER+"_FILE")]
            try:
                hier_raw = Persistence.read_file(f)
                keyword_hier = ExifTool.create_metahierarchy_from_str(hier_raw)
            except:
                keyword_hier = {}
        
        input_dict[Controller.TEMPLATE_KEYWORD_HIER] = keyword_hier
         
        # get default metadata (keyword and others) from file
        meta = {}
        if  is_file(Controller.TEMPLATE_META):
            f = template_dict[(Controller.TEMPLATE_META+"_FILE")]
            try:
                meta_raw = Persistence.read_file(f)
                meta = ExifTool.arg2dict(meta_raw)
            except:
                meta = {}

        input_dict[Controller.TEMPLATE_META] = meta

        # copy single template parameters with default values
        input_dict[Controller.TEMPLATE_OVERWRITE_KEYWORD]  = template_dict.get(Controller.TEMPLATE_OVERWRITE_KEYWORD,False)
        input_dict[Controller.TEMPLATE_OVERWRITE_META]  = template_dict.get(Controller.TEMPLATE_OVERWRITE_META,False)
        tz = template_dict.get(Controller.TEMPLATE_TIMEZONE,"Europe/Berlin")
        input_dict[Controller.TEMPLATE_TIMEZONE] = tz
        map_detail = template_dict.get(Controller.TEMPLATE_DEFAULT_MAP_DETAIL,18)
        input_dict[Controller.TEMPLATE_DEFAULT_MAP_DETAIL]  = map_detail
        input_dict[Controller.TEMPLATE_CREATE_LATLON]  = template_dict.get(Controller.TEMPLATE_CREATE_LATLON,"C")
        input_dict[Controller.TEMPLATE_DEFAULT_GPS_EXT] = template_dict.get(Controller.TEMPLATE_DEFAULT_GPS_EXT,"geo")
        input_dict[Controller.TEMPLATE_GPS_READ_REMOTE] = template_dict.get(Controller.TEMPLATE_GPS_READ_REMOTE,True)

        # direct input of datetime offset from file
        input_dict[Controller.TEMPLATE_CALIB_OFFSET] = template_dict.get(Controller.TEMPLATE_CALIB_OFFSET,None)

        # calibration image file and date, calculate offset
        if (is_file(Controller.TEMPLATE_CALIB_IMG)) and (input_dict[Controller.TEMPLATE_CALIB_OFFSET] is None): 
            f = template_dict.get((Controller.TEMPLATE_CALIB_IMG+"_FILE"))
            
            # gps time (as stored in template file / read from image)
            dt_gps_s = template_dict.get(Controller.TEMPLATE_CALIB_DATETIME)
            if isinstance(dt_gps_s,str):
                # get date time from image file
                with ExifTool(exiftool_ref) as exif:
                    meta_dict_list = exif.get_metadict_from_img(f)

                try:
                    # datetime of image
                    dt_img_s = meta_dict_list[f]["CreateDate"]
                    # datetime of image(cam) / gps time and offset
                    dt_img = Util.get_datetime_from_string(datetime_s=dt_img_s,local_tz=tz,debug=False)
                    dt_gps = Util.get_datetime_from_string(datetime_s=dt_gps_s,local_tz=tz,debug=False)
                    time_offset = Util.get_time_offset(time_camera=dt_img_s,time_gps=dt_gps_s,debug=False)
                    input_dict[Controller.TEMPLATE_CALIB_IMG]  = dt_img
                    input_dict[Controller.TEMPLATE_CALIB_DATETIME]  = dt_gps                    
                    input_dict[Controller.TEMPLATE_CALIB_OFFSET] = time_offset.total_seconds()
                except:
                    input_dict[Controller.TEMPLATE_CALIB_IMG]  = None
                    input_dict[Controller.TEMPLATE_CALIB_DATETIME]  = None
                    input_dict[Controller.TEMPLATE_CALIB_OFFSET] = 0
        
                
        # read / create default latlon file and get default reverse data
        default_lat_lon = template_dict.get(Controller.TEMPLATE_DEFAULT_LATLON,None)

        if default_lat_lon is not None:
            
            op_default_lat_lon =  template_dict.get(Controller.TEMPLATE_CREATE_DEFAULT_LATLON,Persistence.MODE_READ)
            input_dict[Controller.TEMPLATE_DEFAULT_LATLON]  = default_lat_lon
            input_dict[Controller.TEMPLATE_CREATE_DEFAULT_LATLON]  = op_default_lat_lon
            k = Controller.TEMPLATE_DEFAULT_LATLON+"_FILE"
            f = template_dict.get(k)
            ka = k+"_ACTIONS"
            f_actions = template_dict.get(ka)
            input_dict[k] = f
            input_dict[ka] = f_actions 
            
            save = False
            remote = False

            if ( op_default_lat_lon in f_actions ):

                if op_default_lat_lon in Persistence.ACTIONS_CHANGE_FILE:
                    save = True

                    if not op_default_lat_lon == Persistence.MODE_DELETE:
                        remote = True

                # retrieve the nominatim data either from local file or from service
                if not op_default_lat_lon == Persistence.MODE_DELETE:
                    input_dict[Controller.TEMPLATE_DEFAULT_REVERSE_GEO] = Controller.retrieve_nominatim_reverse(filepath=f,
                                                                            latlon=default_lat_lon,save=save,
                                                                            zoom=map_detail,remote=remote,debug=showinfo)    
                else:
                    print("DELETE OPERATION CURRENTLY NOT SUPPORTED") 

            # file operations not possible
            else:
                print(f"file {f} can be used: {is_file(Controller.TEMPLATE_CREATE_DEFAULT_LATLON)}")
                print(f"file operation {op_default_lat_lon} ({Persistence.MODE_TXT.get(op_default_lat_lon)}), allowed values {f_actions}")

        # get gpx file
        if is_file(Controller.TEMPLATE_GPX):
            k = Controller.TEMPLATE_GPX+"_FILE"
            f = template_dict.get(k,"")
            ka = k+"_ACTIONS"
            input_dict[k] = f
            input_dict[ka] = template_dict.get(ka,"")
            gpx_data = Persistence.read_gpx(gpsx_path=f,debug=showinfo,tz=pytz.timezone(tz))
            input_dict[Controller.TEMPLATE_GPX] = gpx_data

        # get default values from template / initialize
        template_default_values = Controller.get_template_default_values()

        augmented_params = {}

        for k in template_default_values.keys():
            if k in input_dict:
                v = input_dict[k]
            else:
                v = template_default_values[k]
            augmented_params[k] = v

        Util.print_dict_info(d=augmented_params,show_info=showinfo,list_elems=3)        

        return augmented_params
    
    @staticmethod
    def get_template_default_values()->dict:
        """ get predefined template values """

        template_default_values = {}

        for k in Controller.TEMPLATE_PARAMS:
            template_default_values[k] = Controller.TEMPLATE_DEFAULT_VALUES.get(k,None)
        return template_default_values

    @staticmethod
    def augment_meta_data(metadata_list:list,metadata_default_dict:dict,metadata:dict,overwrite_meta=False)->dict:
        """ select the metadata value either from file, template or metadata template """
        
        # metadata_default_dict > template meta data 
        # metadata > from file / will be left as is / nothing required / shown here only for debugging

        augmented_meta = {}

        for metadata_key in metadata_list:
            
            metadata_default = metadata_default_dict.get(metadata_key,None)
            if ( not isinstance(metadata_default,dict) ):
                continue
            
            metavalue_file = metadata.get(metadata_key,None)
            metavalue_template = metadata_default.get("template",None)
            
            # get values
            metavalue = None            
            
            # set default values metadata value in template file is prioritized over default metadata value
            if metadata_default_dict is not None:
                metavalue = metadata_default_dict
            if metavalue_template is not None:
                metavalue = metavalue_template
            
            if not ( metavalue_file is None or metavalue is None): # metadata existent
                if not overwrite_meta: # do not overwrite with template value
                    metavalue = None

            # set the new meta value
            if not metavalue is None:
                augmented_meta[metadata_key] = metavalue

        return augmented_meta

    @staticmethod
    def augment_gps_data(fileref:str,geo_dict:dict,template_dict:dict,metadata_dict:dict,utc_timestamp:int=None,debug=False,verbose=False):
        """ blend default and gps data """

        # geo metadata handling deactivated
        if not ( template_dict.get(Controller.TEMPLATE_CREATE_GEO_METADATA,False) ):
            return metadata_dict

        # check if gps metadata are already stored in metadata and still need to be processed 
        lat_ref = metadata_dict.get("GPSLatitudeRef",None)
        lon_ref = metadata_dict.get("GPSLongitudeRef",None)
        lat = metadata_dict.get("GPSLatitude",None)
        lon = metadata_dict.get("GPSLongitude",None)
        gps_metadata_exist = True

        if ( ( lat_ref is None ) or ( lon_ref is None ) or ( lat is None ) or ( lon is None ) ):
             gps_metadata_exist = False       

        # get metadata for overwrite
        overwrite_meta = template_dict.get(Controller.TEMPLATE_OVERWRITE_META,False)

        if ( overwrite_meta is False ) and ( gps_metadata_exist is True ) :
            return metadata_dict

        # get default reverse Geo Data
        default_reverse_geo = template_dict.get(Controller.TEMPLATE_DEFAULT_REVERSE_GEO,None)

        # get the geo filepath / check if file exists already
        file_info = Persistence.get_filepath_info(fileref)
        filepath = file_info.get(Persistence.FILEINFO_FILEPATH,None)
        file_suffix_len = len(file_info.get(Persistence.FILEINFO_SUFFIX))
        
        geo_suffix = template_dict.get(Controller.TEMPLATE_DEFAULT_GPS_EXT,"geo")
        filepath_geo = filepath[:-file_suffix_len]+geo_suffix
        file_info_geo = Persistence.get_filepath_info(filepath_geo)
        geo_exists = file_info_geo.get(Persistence.FILEINFO_EXISTS,False) 

        create_latlon_file = template_dict.get(Controller.TEMPLATE_CREATE_LATLON,Persistence.MODE_IGNORE) 
        geo_detail_level = template_dict.get(Controller.TEMPLATE_DEFAULT_MAP_DETAIL,18) 
        
        # get lat lon data
        try:
            latlon = [geo_dict["lat"],geo_dict["lon"]]
        except:
            latlon = None
        
        # get altitude
        try:
            altitude = geo_dict["ele"]
        except:
            altitude = 0

        # save latlon file
        if create_latlon_file in Persistence.ACTIONS_CHANGE_FILE:
            save_latlon = True
        else:
            save_latlon = False
        
        # read data from file / from url
        reverse_geo = Controller.retrieve_nominatim_reverse(filepath=filepath_geo,latlon=latlon,save=save_latlon,
                                                            zoom=geo_detail_level,remote=(not geo_exists),debug=debug)

        # if nothing found, fallback to default reverse geo data
        if ( not reverse_geo ) and default_reverse_geo:
            if debug:
                print("  ---- NO GPS DATA FOUND, WILL BE REPLACED BY DEFAULT GPS DATA ----")
            reverse_geo = default_reverse_geo
            latlon = default_reverse_geo.get("latlon",None)

        # return empty reverse geo
        if not ( reverse_geo ):
            return {}

        # get reverse metadata as IPTC data 
        reverse_geo_dict = ExifTool.map_geo2exif(reverse_geo)

        # add additional parameters     
        geo_additional = Geo.get_exifmeta_from_latlon(latlon=latlon,altitude=altitude,timestamp=utc_timestamp)    
        reverse_geo_dict.update(geo_additional)
 
        if verbose:
            print("  ---- Exiftool.map_geo2exif ----")
            Util.print_dict_info(reverse_geo_dict)
    
        return reverse_geo_dict

    @staticmethod
    def prepare_img_write(params:dict,debug=False,verbose=False,meta_txt=True):
        """ blend template and metadata for each image file """
        
        now = datetime.now()
        date_s = now.strftime("%Y:%m:%d")

        workdir = params[Controller.TEMPLATE_WORK_DIR]
        exif_ref = params[Controller.TEMPLATE_EXIFTOOL]
        ext = params[Controller.TEMPLATE_IMG_EXTENSIONS]
        gpx = params[Controller.TEMPLATE_GPX]
        timezone = params[Controller.TEMPLATE_TIMEZONE]

        # get default metadata from file / keys are IPTC attributes
        default_meta = params[Controller.TEMPLATE_META]
        overwrite_meta = params[Controller.TEMPLATE_OVERWRITE_META]
        overwrite_keyword = params[Controller.TEMPLATE_OVERWRITE_KEYWORD]
        keyword_hier = params[Controller.TEMPLATE_KEYWORD_HIER]
        default_keywords = default_meta.get("Keywords",[])
        write_tech_keywords = params[Controller.TEMPLATE_TECH_KEYWORDS]

        # gps data / calculate time offset (calculated in prepare_execution) 
        gps_datetime_image = params[Controller.TEMPLATE_CALIB_IMG]
        gps_datetime = params[Controller.TEMPLATE_CALIB_DATETIME]
        gps_offset = params[Controller.TEMPLATE_CALIB_OFFSET]

        # extension for metadata file
        meta_ext = params.get(Controller.TEMPLATE_DEFAULT_META_EXT,"meta")

        # author and copyright info
        copyright_template = params.get(Controller.TEMPLATE_COPYRIGHT,"")
        copyright_notice_template = params.get(Controller.TEMPLATE_COPYRIGHT_NOTICE,"")
        credit_template = params.get(Controller.TEMPLATE_CREDIT,"")
        source_template = params[Controller.TEMPLATE_SOURCE]
        transmission = params.get(Controller.TEMPLATE_TRANSMISSION,"")+" "+date_s
        byline = copyright_template
        byline_title = params.get(Controller.TEMPLATE_BYLINE_TITLE,"")
        writer_editor = params.get(Controller.TEMPLATE_WRITER_EDITOR,"")
        caption_writer = params.get(Controller.TEMPLATE_CAPTION_WRITER,"")
        authors_position = params.get(Controller.TEMPLATE_AUTHORS_POSITION,"")
        user_comment = params.get(Controller.TEMPLATE_USER_COMMENT,"")
        intellectual_genre =  params.get(Controller.TEMPLATE_INTELLECTUAL_GENRE,"")
        web_statement = params.get(Controller.TEMPLATE_WEB_STATEMENT,"")
        usage_terms = params.get(Controller.TEMPLATE_USER_COMMENT,"")
        url_ref = params.get(Controller.TEMPLATE_URL,"")

        # copy default values for metadata (can be either in template or in metadata template)
        default_iptc = {}
        default_iptc["Copyright"] = {"template":copyright_template,"meta":default_meta.get('Copyright',None) }
        default_iptc["CopyrightNotice"] = {"template":copyright_notice_template,"meta":default_meta.get('CopyrightNotice',None) }
        default_iptc["Credit"] = {"template":credit_template,"meta":default_meta.get('Credit',None) }
        default_iptc["Source"] = {"template":source_template,"meta":default_meta.get('Source',None) }
        default_iptc["OriginalTransmissionReference"] = {"template":transmission,"meta":default_meta.get('OriginalTransmissionReference',None) }
        default_iptc["DateCreated"] = {"template":date_s,"meta":default_meta.get('DateCreated',None) }
        default_iptc["By-line"] = {"template":byline,"meta":default_meta.get('By-line',None) }
        default_iptc["By-lineTitle"] = {"template":byline_title,"meta":default_meta.get('By-lineTitle',None) }
        default_iptc["Writer-Editor"] = {"template":writer_editor,"meta":default_meta.get('Writer-Editor',None) }
        default_iptc["CaptionWriter"] = {"template":caption_writer,"meta":default_meta.get('CaptionWriter',None) }
        default_iptc["AuthorsPosition"] = {"template":authors_position,"meta":default_meta.get('AuthorsPosition',None) }      
        default_iptc["UserComment"] = {"template":user_comment,"meta":default_meta.get('UserComment',None) }    
        default_iptc["IntellectualGenre"] = {"template":intellectual_genre,"meta":default_meta.get('IntellectualGenre',None) } 
        default_iptc["WebStatement"] = {"template":web_statement,"meta":default_meta.get('WebStatement',None) } 
        default_iptc["UsageTerms"] = {"template":usage_terms,"meta":default_meta.get('UsageTerms',None) } 
        default_iptc["URL"] = {"template":url_ref,"meta":default_meta.get('URL',None) } 

        if not gpx is None:
            gpx_keys = sorted(gpx.keys())
        else:    
            gpx_keys = []
        
        metadata_filter = ExifTool.IMG_SEGMENT

        if (workdir is None) or (exif_ref is None):
            print(f"Exiftool: {exif_ref} Work Dir: {workdir}, run can't be executed")
            return None

        if debug:
            print(f"\n\n###### READING IMAGES in {workdir} ######\n")
        
        # read all metadata
        with ExifTool(exif_ref,debug=debug) as exif:
            img_meta_list = exif.get_metadict_from_img(filenames=workdir,metafilter=metadata_filter,filetypes=ext)

        if debug:
            if isinstance(img_meta_list,dict):
                print(f"\n\n###### Number of images ({len(img_meta_list.keys())}) ######")
            print(f"     GPS Datetime: {gps_datetime} GPS Datetime Image: {gps_datetime_image}  Offset: {gps_offset}s")
            print(f"     Template Metadata {default_meta}")
            print(f"     Overwrite existing keywords: {overwrite_keyword} Overwrite existing IPTC metadata: {overwrite_meta} Write Tech Keywords {write_tech_keywords}")
            print(f"     COPYRIGHT INFO {copyright_template} notice {copyright_notice_template} credit {credit_template} source {source_template}")


        for fileref,metadata_dict in img_meta_list.items():

            creation_date = metadata_dict.get("CreateDate",None)
            creation_timestamp = Util.get_localized_datetime(dt_in=creation_date,tz_in=timezone,tz_out="UTC",
                                                             debug=False,as_timestamp=True) 
            if not ( creation_timestamp is None or gps_offset is None ):                                                 
                creation_timestamp = int(creation_timestamp) + int(gps_offset)                                    
                                                            
            if isinstance(creation_timestamp,int):
                creation_datetime = datetime.utcfromtimestamp(creation_timestamp)
            else:
                creation_datetime = None

            timestamp_index = None
            timestamp_gpx = None
            datetime_gpx = None
            geo_data = None            
            timestamp_index = Util.get_nearby_index(creation_timestamp,sorted_list=gpx_keys,debug=False)            
            
            if timestamp_index != Util.NOT_FOUND:
                timestamp_gpx = gpx_keys[timestamp_index]
                datetime_gpx = datetime.utcfromtimestamp(timestamp_gpx)
                geo_data = gpx[timestamp_gpx]

            # get technical keywords
            tech_keywords,tech_hierarchy = ExifTool.get_tech_keywords_from_metadict(metadata_dict,debug=verbose)

            keywords = []
            if (len(tech_hierarchy)==0):
                hier_keywords = []
            else:
                hier_keywords = [*tech_hierarchy]

            file_keywords = metadata_dict.get("Keywords",[])
            if not overwrite_keyword:
                keywords = [*keywords,*file_keywords]

            keywords = [*keywords,*default_keywords]

            # get metadata from template and from file / augment metadata
            if write_tech_keywords:
                keywords = [*keywords,*tech_keywords] 

            #get hierarchical metadata
            for keyword in keywords:
                hier_keyword = keyword_hier.get(keyword,None)
                if hier_keyword is not None:
                    hier_keywords.append(hier_keyword)

            # augment metadata
            augmented_meta = Controller.augment_meta_data(metadata_list=ExifTool.IMG_SEG_AUGMENTED,metadata_default_dict=default_iptc,
                                                         metadata=metadata_dict,overwrite_meta=overwrite_meta)
            
            # gps metadata
            gps_data = Controller.augment_gps_data(fileref=fileref,geo_dict=geo_data,template_dict=params,metadata_dict=metadata_dict,utc_timestamp=creation_timestamp,debug=False) 

            # gps keywords
            try:
                geo_keywords = gps_data.pop("Keywords")
            except:
                 geo_keywords = None

            try:
                geo_hier_keyword = gps_data.pop("HierarchicalSubject")
            except:
                geo_hier_keyword = None
        
            if isinstance(geo_keywords,list):
                keywords.extend(geo_keywords)
            
            if (isinstance(geo_hier_keyword,str)):
                hier_keywords.append(geo_hier_keyword)             

            # remove duplicates
            keywords = list(dict.fromkeys(keywords).keys())
            hier_keywords = list(dict.fromkeys(hier_keywords).keys())

            # add metadata
            augmented_meta["Keywords"] = keywords
            augmented_meta["HierarchicalSubject"] = hier_keywords

            augmented_meta.update(gps_data)

            if debug:
                print(f"\n --- File {fileref} \n          corrected timestamp {creation_timestamp} offset {gps_offset} corrected UTC {creation_datetime} ")
                print(f"                GPS timestamp {timestamp_gpx} UTC {datetime_gpx} \n")     
                if verbose:
                    print("      METADATA STORED IN IMAGE")
                    Util.print_dict_info(d=metadata_dict) 
                    print(f"      GEO Data: {geo_data}")
                    print(f"      Tech Keywords {tech_keywords}")     
                    print(f"      Default Keywords: {default_keywords}")    
                    print(f"      File Keywords: {file_keywords}")     
                    print(f"      All Keywords:  {keywords}")   
                    print(f"      Hierarchy Keywords:  {hier_keywords}")   
                    print("      #### Augmented Metadata: ####\n")
                    Util.print_dict_info(d=augmented_meta) 

            new_metadata = {}
            
            if verbose:
                print("      #### Augmented Metadata: ####\n")

            # now augment all metadata
            for key,new in augmented_meta.items():
                old = metadata_dict.get(key,None)
                if verbose:
                    if old is None:
                        s = "++( NEW )++"
                    else:
                        s = "--( OLD )--"
                    print(f"      {s} KEY {key} OLD {old} -> NEW {new}",end = '')
                
                if ( old is None ) or                                              \
                   ( ( key in ExifTool.META_DATA_LIST ) and overwrite_keyword ) or \
                   ( ( key not in ExifTool.META_DATA_LIST ) and overwrite_meta ):
                    if verbose:
                        print(" // WRITE VALUE //")
                    new_metadata[key] = new
                    continue
                else:
                    if verbose:
                        print(" \\ KEEP OLD VALUE \\")
                
            # get the fileref for properties file
            if meta_txt:
                fp_info_suffix_len = len(Persistence.get_filepath_info(fileref).get("suffix",""))
                fileref_meta = fileref[:(-fp_info_suffix_len)] + meta_ext
                if debug:
                    print(f"      Save metadata to {fileref_meta}")
                try:
                    meta_txt = ExifTool.dict2arg(meta_dict=new_metadata)
                    if verbose:
                        print(f" metadata to be saved: {meta_txt}")
                    Persistence.save_file(data=meta_txt,filename=fileref_meta)
                except:
                    print(f"Exception with file {fileref_meta}, processing will be skipped")
                    print(traceback.format_exc())
        
        return None