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
        
        # Reference to Exif Tool
        tpl_dict["INFO_EXIFTOOL_FILE"] = "INFO: Enter full path to your EXIFTOOL.EXE executable"
        tpl_dict["EXIFTOOL_FILE"] ="exiftool.exe"
        
        # Work Directory
        tpl_dict["INFO_WORK_DIR"] = "INFO: Work Directory, If supplied only file names need to be supplied"
        tpl_dict["WORK_DIR"] = "_workdir_"
        
        # Keywords
        tpl_dict["INFO_KEYWORD_HIER_FILE"] = "INFO: UTF8 Text file containing your metadata keyword hierarchy"
        tpl_dict["KEYWORD_HIER_FILE"] = "_keyword_hier_file_"
        tpl_dict["INFO_KEYWORD_FILE"] = "INFO: UTF8 Text file with default keywords, entry line needs to be in form keywords= ... "
        tpl_dict["KEYWORD_FILE"] = "_keyword_file_"
        
        # Geo Coordinate Handling
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
        tpl_dict["INFO_CREATE_LATLON"] = "Create LATLON FILE, values (0:do nothing,2:read only latlon,1:overwrite and create latlon file )"
        tpl_dict["CREATE_LATLON"] = 1          
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

        IGNORE = ["WORK_DIR","TIMEZONE"]

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

        if showinfo is True:
            print(f"WORKING DIRECTORY -> {work_dir}")
            print(f"TIME ZONE -> {timezone}")

        for k,v in params_raw.items():

            K = k.upper()
            
            if ( "INFO_" in k ) or ( k.upper() in IGNORE ):
                continue 
            
            if showinfo:
                print(f"PARAMETER {K} -> {v}")
            
            # convert datetime fields
            if "DATETIME" in K:
                dt_loc = Util.get_datetime_from_string(datetime_s=v,local_tz=timezone,debug=showinfo)
                control_params[K] = dt_loc
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
                full_path = Persistence.get_file_full_path(filepath=work_dir,filename=v,object_filter=[Persistence.OBJECT_FILE])                
                if showinfo:
                    print(f"   File Parameter {k} points to {full_path}")
                control_params[K] = full_path
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