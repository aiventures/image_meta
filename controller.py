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
    TEMPLATE_IMG_EXTENSIONS = "IMG_EXTENSIONS"
    TEMPLATE_EXIFTOOL = "EXIFTOOL"
    TEMPLATE_META = "META"
    TEMPLATE_OVERWRITE_KEYWORD = "OVERWRITE_KEYWORD"
    TEMPLATE_OVERWRITE_META = "OVERWRITE_META"
    TEMPLATE_KEYWORD_HIER = "KEYWORD_HIER"
    TEMPLATE_TECH_KEYWORDS = "TECH_KEYWORDS"

    # Copyright Fields
    TEMPLATE_COPYRIGHT = "COPYRIGHT"
    TEMPLATE_COPYRIGHT_NOTICE = "COPYRIGHT_NOTICE"
    TEMPLATE_CREDIT = "CREDIT"
    TEMPLATE_SOURCE = "SOURCE"

    # Geocoordinate Handling
    TEMPLATE_TIMEZONE = "TIMEZONE"
    TEMPLATE_CALIB_IMG = "CALIB_IMG"
    TEMPLATE_CALIB_DATETIME = "CALIB_DATETIME"
    TEMPLATE_CALIB_OFFSET = "CALIB_OFFSET"
    TEMPLATE_GPX = "GPX"
    TEMPLATE_DEFAULT_LATLON = "DEFAULT_LATLON"
    TEMPLATE_CREATE_LATLON = "CREATE_LATLON"    
    TEMPLATE_CREATE_DEFAULT_LATLON = "CREATE_DEFAULT_LATLON"  
    TEMPLATE_DEFAULT_MAP_DETAIL = "DEFAULT_MAP_DETAIL"
    TEMPLATE_DEFAULT_REVERSE_GEO = "DEFAULT_REVERSE_GEO"


    TEMPLATE_PARAMS = [TEMPLATE_WORK_DIR,TEMPLATE_IMG_EXTENSIONS,TEMPLATE_EXIFTOOL, TEMPLATE_META, TEMPLATE_OVERWRITE_KEYWORD, 
                       TEMPLATE_OVERWRITE_META, TEMPLATE_KEYWORD_HIER, TEMPLATE_TECH_KEYWORDS, TEMPLATE_COPYRIGHT, 
                       TEMPLATE_COPYRIGHT_NOTICE, TEMPLATE_CREDIT, TEMPLATE_SOURCE, TEMPLATE_TIMEZONE,
                       TEMPLATE_CALIB_IMG, TEMPLATE_CALIB_DATETIME,TEMPLATE_CALIB_OFFSET,TEMPLATE_GPX, 
                       TEMPLATE_DEFAULT_LATLON,TEMPLATE_CREATE_LATLON,
                       TEMPLATE_CREATE_DEFAULT_LATLON,TEMPLATE_DEFAULT_MAP_DETAIL]
    
    # mapping template values to meta data
    TEMPLATE_META_MAP = {}

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
        tz = template_dict.get(Controller.TEMPLATE_TIMEZONE,"Europe/Berlin")
        input_dict[Controller.TEMPLATE_TIMEZONE] = tz
        map_detail = template_dict.get(Controller.TEMPLATE_DEFAULT_MAP_DETAIL,18)
        input_dict[Controller.TEMPLATE_DEFAULT_MAP_DETAIL]  = map_detail
        input_dict[Controller.TEMPLATE_CREATE_LATLON]  = template_dict.get(Controller.TEMPLATE_CREATE_LATLON,"C")

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
        
        Util.print_dict_info(d=input_dict,show_info=showinfo,list_elems=3)

        return input_dict        
    
    @staticmethod
    def get_template_default_values()->dict:
        """ get predefined template values """
        template_default_values = {}
        for template_value in Controller.TEMPLATE_PARAMS:
            v = None
            if template_value == Controller.TEMPLATE_IMG_EXTENSIONS:
                v = ["jpg","jpeg"]
            elif template_value == Controller.TEMPLATE_TIMEZONE:
                v = "Europe/Berlin"
            elif template_value == Controller.TEMPLATE_OVERWRITE_KEYWORD:
                v = False
            elif template_value == Controller.TEMPLATE_OVERWRITE_META:
                v = False   
            elif template_value == Controller.TEMPLATE_TECH_KEYWORDS:
                v = True
            elif template_value == Controller.TEMPLATE_COPYRIGHT:
                v = "Unknown Artist"
            elif template_value == Controller.TEMPLATE_COPYRIGHT_NOTICE:
                v = "All rights reserved"
            elif template_value == Controller.TEMPLATE_CREDIT:
                v = "Unknown Artist"
            elif template_value == Controller.TEMPLATE_SOURCE:
                v = "Own Photography"            
            elif template_value == Controller.TEMPLATE_CREATE_DEFAULT_LATLON:
                v = True
            elif template_value == Controller.TEMPLATE_DEFAULT_MAP_DETAIL:
                v = 17
            elif template_value == Controller.TEMPLATE_KEYWORD_HIER:
                v = {}
            elif template_value == Controller.TEMPLATE_CALIB_OFFSET:
                v = 0
            template_default_values[template_value] = v
        return template_default_values

    @staticmethod
    def get_metadata_from_template(params:dict):
        """ Creates IPTC metadata values from template """
        template_metadata = {}

        #  'META',
        #  'COPYRIGHT',
        #  'COPYRIGHT_NOTICE',
        #  'CREDIT',
        #  'SOURCE'

        for template_value in params.keys():
            pass

        return template_metadata

    @staticmethod
    def prepare_img_write(params:dict,show_info=False):
        """ blend template and metadata for each image file """
        

    # TEMPLATE_PARAMS = [TEMPLATE_OVERWRITE_KEYWORD, 
    #                    TEMPLATE_OVERWRITE_META, TEMPLATE_KEYWORD_HIER, TEMPLATE_TECH_KEYWORDS, TEMPLATE_COPYRIGHT, 
    #                    TEMPLATE_COPYRIGHT_NOTICE, TEMPLATE_CREDIT, TEMPLATE_SOURCE, TEMPLATE_TIMEZONE,
    #                    TEMPLATE_CALIB_IMG, TEMPLATE_CALIB_DATETIME,TEMPLATE_GPX, TEMPLATE_DEFAULT_LATLON,TEMPLATE_CREATE_LATLON,
    #                    TEMPLATE_CREATE_DEFAULT_LATLON,TEMPLATE_DEFAULT_MAP_DETAIL]
        
        # get default values from template / initialize
        template_default_values = Controller.get_template_default_values()
        augmented_params = {}
        for k in template_default_values.keys():
            if k in params:
                v = params[k]
            else:
                v = template_default_values[k]
            augmented_params[k] = v

        workdir = augmented_params[Controller.TEMPLATE_WORK_DIR]
        exif_ref = augmented_params[Controller.TEMPLATE_EXIFTOOL]
        ext = augmented_params[Controller.TEMPLATE_IMG_EXTENSIONS]
        gpx = augmented_params[Controller.TEMPLATE_GPX]
        timezone = augmented_params[Controller.TEMPLATE_TIMEZONE]

        # get default metadata from file / keys are IPTC attributes
        default_meta = augmented_params[Controller.TEMPLATE_META]
        overwrite_meta = augmented_params[Controller.TEMPLATE_OVERWRITE_META]
        overwrite_keyword = augmented_params[Controller.TEMPLATE_OVERWRITE_KEYWORD]
        keyword_hier = augmented_params[Controller.TEMPLATE_KEYWORD_HIER]
        default_keywords = default_meta.get("Keywords",[])
        write_tech_keywords = augmented_params[Controller.TEMPLATE_TECH_KEYWORDS]
        
        # gps data / calculate time offset (calculated in prepare_execution) 
        gps_datetime_image = augmented_params[Controller.TEMPLATE_CALIB_IMG]
        gps_datetime = augmented_params[Controller.TEMPLATE_CALIB_DATETIME]
        gps_offset = augmented_params[Controller.TEMPLATE_CALIB_OFFSET]

        if not gpx is None:
            gpx_keys = sorted(gpx.keys())
        else:    
            gpx_keys = []
        
        metadata_filter = ExifTool.IMG_SEGMENT

        if (workdir is None) or (exif_ref is None):
            print(f"Exiftool: {exif_ref} Work Dir: {workdir}, run can't be executed")
            return None

        # read all metadata
        with ExifTool(exif_ref,debug=show_info) as exif:
            img_meta_list = exif.get_metadict_from_img(filenames=workdir,metafilter=metadata_filter,filetypes=ext)

        if show_info:
            if isinstance(img_meta_list,dict):
                print(f"\n\n---- Number of images ({len(img_meta_list.keys())}) ----")
            print(f"     GPS Datetime: {gps_datetime} GPS Datetime Image: {gps_datetime_image}  Offset: {gps_offset}s")
            print(f"     Template Metadata {default_meta}")
            print(f"     Overwrite existing keywords: {overwrite_keyword} Overwrite existing IPTC metadata: {overwrite_meta} Write Tech Keywords {write_tech_keywords}")

        for fileref,metadata_list in img_meta_list.items():
            creation_date = metadata_list.get("CreateDate",None)
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
            gpx_data = None            
            timestamp_index = Util.get_nearby_index(creation_timestamp,sorted_list=gpx_keys,debug=False)            
            
            if timestamp_index != Util.NOT_FOUND:
                timestamp_gpx = gpx_keys[timestamp_index]
                datetime_gpx = datetime.utcfromtimestamp(timestamp_gpx)
                gpx_data = gpx[timestamp_gpx]

            # get technical keywords
            tech_keywords = ExifTool.get_tech_keywords_from_metadict(metadata_list)

            # get metadata from template and from file / augment metadata
            keywords = []
            file_keywords = metadata_list.get("Keywords",[])

            if show_info:
                print(f"\n --- File {fileref} \n          corrected timestamp {creation_timestamp} offset {gps_offset} corrected UTC {creation_datetime} ")
                print(f"                GPS timestamp {timestamp_gpx} UTC {datetime_gpx} \n      GPS DATA:",gpx_data)     
                print(f"      Tech Keywords {tech_keywords}")     
                print(f"      Default Keywords: {default_keywords}")    
                print(f"      File Keywords: {file_keywords}")     

            #get hierarchical metadata
            #copyright info
            #gps metadata
            #read reverse geo info     

        return None