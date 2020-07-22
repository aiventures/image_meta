""" module to handle overall execution of EXIF handling """

import os
import pytz
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
    TEMPLATE_EXIFTOOL = "EXIFTOOL"
    TEMPLATE_META = "META"
    TEMPLATE_OVERWRITE_KEYWORD = "OVERWRITE_KEYWORD"
    TEMPLATE_KEYWORD_HIER = "KEYWORD_HIER"
    TEMPLATE_TIMEZONE = "TIMEZONE"
    TEMPLATE_CALIB_IMG = "CALIB_IMG"
    TEMPLATE_CALIB_DATETIME = "CALIB_DATETIME"
    TEMPLATE_CALIB_OFFSET = "CALIB_OFFSET"
    TEMPLATE_GPX = "GPX"
    TEMPLATE_DEFAULT_LATLON = "DEFAULT_LATLON"
    TEMPLATE_CREATE_LATLON = "CREATE_LATLON"    
    TEMPLATE_DEFAULT_MAP_DETAIL = "DEFAULT_MAP_DETAIL"
    TEMPLATE_DEFAULT_REVERSE_GEO = "DEFAULT_REVERSE_GEO"
    TEMPLATE_PARAMS = [TEMPLATE_WORK_DIR,TEMPLATE_EXIFTOOL, TEMPLATE_META, TEMPLATE_OVERWRITE_KEYWORD, TEMPLATE_KEYWORD_HIER, TEMPLATE_TIMEZONE,
                       TEMPLATE_CALIB_IMG, TEMPLATE_CALIB_DATETIME,TEMPLATE_GPX, TEMPLATE_DEFAULT_LATLON,TEMPLATE_CREATE_LATLON,TEMPLATE_DEFAULT_MAP_DETAIL]

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
        
        # Keywords / KEYWORD KEYWORD_HIER
        tpl_dict["INFO_KEYWORD_HIER_FILE"] = "INFO: UTF8 Text file containing your metadata keyword hierarchy"
        tpl_dict["KEYWORD_HIER_FILE"] = "_keyword_hier_file_"
        tpl_dict["INFO_META_FILE"] = "INFO: UTF8 Text file with additonal meta data, each entry line needs to be in args format, eg '-keywords=...'"
        tpl_dict["META_FILE"] = "_meta_file_"
        tpl_dict["INFO_OVERWRITE_KEYWORD"] = "INFO: Overwrite Keywords / Hier Subject or append from meta file "
        tpl_dict["OVERWRITE_KEYWORD"] = False
        
        # Geo Coordinate Handling / 
        tpl_dict["INFO_CALIB_IMG_FILE"] = "INFO: image displaying time of your GPS "
        tpl_dict["CALIB_IMG_FILE"] = "gps.jpg"
        tpl_dict["INFO_CALIB_DATETIME"] = "INFO: Enter Date Time displayed by your GPS image in Format with Quotes 'YYYY:MM:DD HH:MM:SS' "
        tpl_dict["CALIB_DATETIME"] = datetime.now().strftime("%Y:%m:%d %H:%M:%S")     
        tpl_dict["INFO_TIMEZONE"] = "INFO: Enter Time Zone (values as defined by pytz), default is 'Europe/Berlin'"
        tpl_dict["TIMEZONE"] = "Europe/Berlin"
        tpl_dict["INFO_GPX_FILE"] = "INFO: Filepath to your gpx file from your gps device"
        tpl_dict["GPX_FILE"] = "geo.gpx"       
        tpl_dict["INFO_DEFAULT_LATLON"] = "DEFAULT LAT LON COORDINATES if Geocoordinates or GPX Data can't be found"
        tpl_dict["DEFAULT_LATLON"] = (49.01304,8.40433)  
        tpl_dict["INFO_CREATE_LATLON"] = "Create LATLON FILE, values (0:ignore, C:create, R:read , U:update"
        tpl_dict["CREATE_LATLON"] = Persistence.MODE_CREATE     
        tpl_dict["INFO_DEFAULT_LATLON_FILE"] = "DEFAULT LAT LON FILE PATH for Default Geocoordinates if they can't be found"
        tpl_dict["DEFAULT_LATLON_FILE"] = "default.gps"          
        tpl_dict["INFO_DEFAULT_MAP_DETAIL"] = "DEFAULT Detail level for map links (1...18)"
        tpl_dict["DEFAULT_MAP_DETAIL"] = 18     

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

        IGNORE = ["WORK_DIR","TIMEZONE","CREATE_LATLON"]

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

        create_latlon = params_raw.get("CREATE_LATLON",Persistence.MODE_READ)
        control_params["CREATE_LATLON"] = create_latlon
        control_params["CREATE_LATLON_TEXT"] = Persistence.MODE_TXT.get(create_latlon,"NA")

        if showinfo is True:
            print(f"WORKING DIRECTORY -> {work_dir}")
            print(f"TIME ZONE -> {timezone}")
            print(f"CREATE LATLON DEFAULT FILE -> {create_latlon} ({Persistence.MODE_TXT[create_latlon]})")

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

                object_filter_list=[Persistence.OBJECT_FILE]
                if K == "DEFAULT_LATLON_FILE":

                    # read is default 
                    object_filter_list = [Persistence.OBJECT_FILE] 

                    if create_latlon == Persistence.MODE_IGNORE:
                        object_filter_list = [] 
                    elif create_latlon == Persistence.MODE_CREATE:
                        object_filter_list = [Persistence.OBJECT_FILE,Persistence.OBJECT_NEW_FILE]      
                
                for object_filter in object_filter_list:
                    object_filter_s = [object_filter]     
                    full_path = Persistence.get_file_full_path(filepath=work_dir,filename=v,object_filter=object_filter_s,showinfo=False)    
                    if not full_path is None:
                        control_params[K] = full_path
                        key_file_info = K+"_OBJECT"
                        control_params[key_file_info] = object_filter_s[0]
                        if showinfo:
                            print(f"   File Parameter {k} points to {full_path} (object {object_filter_s})")
                    
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
        
        # try to read from file 1st  
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
            geo_dict = Geo.geo_reverse_from_nominatim(latlon,zoom=zoom,debug=debug)

        if ((save is True) and (filepath is not None)):
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

        def param_has_fileref(param):
            key = param + "_FILE_OBJECT"
            return ( ( template_dict.get(key,None) == Persistence.OBJECT_FILE ) or
                     ( template_dict.get(key,None) == Persistence.OBJECT_NEW_FILE ) )
        
        input_dict = {}

        # get exiftool availability
        if param_has_fileref(Controller.TEMPLATE_EXIFTOOL):            
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

        # read keyword hierarchy
        keyword_hier = {}

        if param_has_fileref(Controller.TEMPLATE_KEYWORD_HIER):
            f = template_dict[(Controller.TEMPLATE_KEYWORD_HIER+"_FILE")]
            try:
                hier_raw = Persistence.read_file(f)
                keyword_hier = ExifTool.create_metahierarchy_from_str(hier_raw)
            except:
                keyword_hier = {}
        
        input_dict[Controller.TEMPLATE_KEYWORD_HIER] = keyword_hier
         
        # get default metadata (keyword and others) from file
        meta = {}
        if param_has_fileref(Controller.TEMPLATE_META):
            f = template_dict[(Controller.TEMPLATE_META+"_FILE")]
            try:
                meta_raw = Persistence.read_file(f)
                meta = ExifTool.arg2dict(meta_raw)
            except:
                meta = {}

        input_dict[Controller.TEMPLATE_META] = meta

        # copy single template parameters with default values
        # TEMPLATE_SINGLE_PARAMS = [TEMPLATE_OVERWRITE_KEYWORD,TEMPLATE_TIMEZONE,TEMPLATE_DEFAULT_MAP_DETAIL]
        input_dict[Controller.TEMPLATE_OVERWRITE_KEYWORD]  = template_dict.get(Controller.TEMPLATE_OVERWRITE_KEYWORD,False)
        input_dict[Controller.TEMPLATE_TIMEZONE]  = template_dict.get(Controller.TEMPLATE_TIMEZONE,"Europe/Berlin")
        map_detail = template_dict.get(Controller.TEMPLATE_DEFAULT_MAP_DETAIL,18)
        input_dict[Controller.TEMPLATE_DEFAULT_MAP_DETAIL]  = map_detail

        # calibration image file and date, calculate offset
        if param_has_fileref(Controller.TEMPLATE_CALIB_IMG): 
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
                    #time zone
                    tz = input_dict[Controller.TEMPLATE_TIMEZONE]
                    # datetime of image(cam) / gps time and offset
                    dt_img = Util.get_datetime_from_string(datetime_s=dt_img_s,local_tz=tz,debug=False)
                    dt_gps = Util.get_datetime_from_string(datetime_s=dt_gps_s,local_tz=tz,debug=False)
                    time_offset = Util.get_time_offset(time_camera=dt_img_s,time_gps=dt_gps_s,debug=False)
                    input_dict[Controller.TEMPLATE_CALIB_IMG]  = dt_img
                    input_dict[Controller.TEMPLATE_CALIB_DATETIME]  = dt_gps
                    input_dict[Controller.TEMPLATE_CALIB_OFFSET] = time_offset
                except:
                    input_dict[Controller.TEMPLATE_CALIB_IMG]  = None
                    input_dict[Controller.TEMPLATE_CALIB_DATETIME]  = None
                    input_dict[Controller.TEMPLATE_CALIB_OFFSET] = 0
        
                
        # read / create default latlon file and get default reverse data
        default_lat_lon = template_dict.get(Controller.TEMPLATE_DEFAULT_LATLON,None)
        
        if default_lat_lon is not None:
            create_lat_lon =  template_dict.get(Controller.TEMPLATE_CREATE_LATLON,Persistence.MODE_READ)
            input_dict[Controller.TEMPLATE_DEFAULT_LATLON]  = default_lat_lon
            input_dict[Controller.TEMPLATE_CREATE_LATLON]  = create_lat_lon
            

            if param_has_fileref(Controller.TEMPLATE_DEFAULT_LATLON):
                k = Controller.TEMPLATE_DEFAULT_LATLON+"_FILE"
                f = template_dict.get(k)
                input_dict[k] = f 
                ko = Controller.TEMPLATE_DEFAULT_LATLON+"_FILE_OBJECT"
                fo = template_dict.get(ko)
                input_dict[ko] = fo 
                
                remote = False
                save = False
                
                # create /update: get latlon from service, save 
                if ( ( fo == Persistence.OBJECT_NEW_FILE and create_lat_lon == Persistence.MODE_CREATE ) or
                   ( fo == Persistence.OBJECT_FILE and create_lat_lon in "CU" ) ):
                    remote = True
                    save = True
                
                # retrieve the nominatim data either from local file or from service
                if create_lat_lon in "CRU":
                    input_dict[Controller.TEMPLATE_DEFAULT_REVERSE_GEO] = Controller.retrieve_nominatim_reverse(filepath=f,
                                                                            latlon=default_lat_lon,save=save,
                                                                            zoom=map_detail,remote=remote,debug=False)         

        # get gpx file


        return input_dict        