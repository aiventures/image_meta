""" module to handle exif data (with EXIF Tool) """

import subprocess
import os
import json
import traceback
from datetime import datetime
from image_meta.persistence import Persistence
from image_meta.util import Util
from image_meta.geo import Geo
from pathlib import Path

class ExifTool(object):
    """ Interface to EXIF TOOL"""

    # Summary: What are methods doing? 
    # 1a get_metadict_from_img: *[File]jpg > dictionary[filepath]:exif_data (get_meta_args)
    # 1b get_metadict_from_img2: *[File]jpg > [data]EXIF_DATA(json) >  dictionary[filepath]:exif_data (get_metadata)
    # 2 write_args_from_img:  *[File]jpg  > get_metadict_from_img > *[File]args (write_args)
    # 3 write_args2img: > *[File]args  > EXIF_DATA > *[File]jpg (write_args2meta)
    # 4 arg2dict: *[data]args > *[data]dictionary
    # 5 dict2arg: *[data]dictionary > *[data]args
    # 6 create_metahierarchy_from_file: *[File]Metadata Hierarchy > *[data]etahierarchy_dictionary (create_meta_hierarchy_tags)
    # EXIF / IIM Specification and Examples http://www.iptc.org/std/IIM/4.2/specification/IIMV4.2.pdf 

    SENTINEL = "{ready}\r\n"
    SEPARATOR = os.sep
    EXIF_LIST_SEP = ", "
    HIER_SEP = "|"
    NEW_LINE = "\r\n"
    ARGS = "args"
    COPYRIGHT = u'©'
    IMG_FILE_TYPES = ["jpg","jpeg","tif","tiff","ARW"]

    # relevant metadata definitions, for specification check  
    # https://www.iptc.org/std/photometadata/documentation/
    # https://exiftool.org/TagNames/IPTC.html
    # https://de.wikipedia.org/wiki/Exchangeable_Image_File_Format

    # general metadata fields
    # [IPTC]          ObjectName                      : _TITEL
    # [XMP]           Title                           : _TITEL
    # [EXIF]          UserComment                     : _BENUTZERKOMMENTAR
    # [XMP]           Label                           : _BESCHRIFTUNG
    # [EXIF]          ImageDescription                : _BILDUNTERSCHRIFT
    # [IPTC]          Caption-Abstract                : _BILDUNTERSCHRIFT
    # [XMP]           Description                     : _BILDUNTERSCHRIFT
    # [IPTC]          Headline                        : _IPTC_ÜBERSCHRIFT
    # [EXIF]          Artist                          : _ERSTELLER
    # [IPTC]          By-line                         : _ERSTELLER
    # [XMP]           Creator                         : _ERSTELLER
    # [XMP]           Rights                          : _IPTC_WF_COPYRIGHT
    # [EXIF]          Copyright                       : _IPTC_WF_COPYRIGHT
    # [XMP]           CaptionWriter                   : _IPTC_AUTOR_BESCHREIBUNG
    # [XMP]           UsageTerms                      : _IPTC_WF_BED_RECHTENUITZUNGEN
    # [IPTC]          Credit                          : _IPTC_WF_BILDRECHTE
    # [IPTC]          Source                          : _IPTC_WF_QUELLE
    # [IPTC]          CopyrightNotice                 : _IPTC_WF_COPYRIGHT
    # [IPTC]          Writer-Editor                   : _IPTC_AUTOR_BESCHREIBUNG
    # [XMP]           Subject                         : <keywords> 
    # [IPTC]          Keywords                        : <keywords> 
    # [XMP]           HierarchicalSubject             : <hier_keywords>
    # [XMP]           State                           : _IPTC_BUNDESLAND
    # [XMP]           Country                         : _IPTC_LAND
    # [XMP]           Location                        : _IPTC_ORTSDETAIL
    # [XMP]           CountryCode                     : DE
    # [IPTC]          City                            : _IPTC_STADT
    # [IPTC]          Sub-location                    : _IPTC_ORTSDETAIL
    # [IPTC]          Province-State                  : _IPTC_BUNDESLAND
    # [IPTC]          Country-PrimaryLocationCode     : DE
    # [IPTC]          Country-PrimaryLocationName     : _IPTC_LAND
    # [Composite]     GPSLatitude                     : lat 
    # [Composite]     GPSLongitude                    : lon
    # [Composite]     GPSPosition                     : lat lon 48
    # [EXIF]          GPSVersionID                    : 2.2.0.0
    # [EXIF]          GPSLatitudeRef                  : North
    # [EXIF]          GPSLongitudeRef                 : East
    # [EXIF]          GPSAltitude                     : 588.5435 m
    # [EXIF]          GPSImgDirection                 : 45
    # [Photoshop]     IPTCDigest                      : 098b116a0d6a73a5c032bddf81fd41ce

    # Processing
    IMG_SEGMENT_PRC = ['ExifToolVersion', 'XMPToolkit', 'FileType', 'FileTypeExtension', 'OriginatingProgram']
    
    # Camera
    IMG_SEGMENT_CAM = [ 'Make', 'Model', 'ExposureTime', 'ShutterSpeedValue', 'ShutterSpeed','ISO','ScaleFactor35efl'
                        ,'ExposureCompensation','FocusMode','CircleOfConfusion']
    # Lens
    IMG_SEGMENT_LNS = [ 'FNumber', 'ApertureValue', 'Aperture','MaxApertureValue', 'FocalLength','LensFormat', 
                        'LensSpecFeatures', 'LensMount2', 'LensMount', 'LensType',   'FOV', 'FocalLength35efl', 
                        'FocalLengthIn35mmFormat', 'HyperfocalDistance', 'LightValue', 'LensID', 
                        'LensSpec', 'LensInfo', 'LensModel']
    # Descriptions
    # 'Subject' [64],'Keywords' [*64],'HierarchicalSubject' [],'ObjectName' [64],
    # 'UserComment' [256] -doesnt support utf8,
    # 'Byline' [32] - Creator Name, 'Headline' [256],'BylineTitle' [32] - Title Of Creator
    # 'Artist' [],'ImageDescription' [],'Caption-Abstract' [2000],'Category' [3]
    IMG_SEGMENT_DSC = ['CurrentIPTCDigest', 'IPTCDigest', 'CodedCharacterSet', 'Subject', 'Keywords', 
                       'HierarchicalSubject', 'ObjectName', 'UserComment', 'Byline', 'Headline', 
                       'BylineTitle', 'Artist', 'ImageDescription', 'Caption-Abstract', 'Category']
    # Author
    # 'WriterEditor' [], 'Copyright' [], 'CopyrightNotice' [128], 'Credit' [32], 'CopyrightFlag' []
    # 'Source' [32], 'EditStatus' [64], 'FixtureIdentifier' [32], 'SpecialInstructions' [256]
    # 'OriginalTransmissionReference' [32]
    IMG_SEGMENT_AUT = ['WriterEditor', 'Copyright', 'CopyrightNotice', 'Credit','CopyrightFlag', 'Source', 
                       'EditStatus', 'FixtureIdentifier', 'SpecialInstructions',  'OriginalTransmissionReference']
    # Location
    # 'City' [32], 'Sublocation' [32], 'ProvinceState' [32]. 'CountryPrimaryLocationCode' [3]
    # 'CountryPrimaryLocationName' [64]
    IMG_SEGMENT_LOC = ['City', 'Sublocation', 'ProvinceState', 'CountryPrimaryLocationCode', 'CountryPrimaryLocationName'] 
    
    # GPS 
    IMG_SEGMENT_GPS = ['GPSVersionID', 'GPSLatitudeRef', 'GPSLongitudeRef', 'GPSAltitudeRef', 'GPSTimeStamp', 'GPSMapDatum', 
                       'GPSDateStamp', 'GPSAltitude', 'GPSDateTime', 'GPSLatitude', 'GPSLongitude', 'GPSPosition']
    # Date
    # 'DateTimeOriginal' [], 'CreateDate' [], 'DateCreated' [CCYYMMDD], 
    # 'TimeCreated' [HHMMSS±HHMM], 'DateTimeCreated' [] 
    IMG_SEGMENT_DATE = ['DateTimeOriginal', 'CreateDate', 'DateCreated', 'TimeCreated', 'DateTimeCreated']
    
    # All Segments
    IMG_SEGMENT = [*IMG_SEGMENT_AUT,*IMG_SEGMENT_CAM,*IMG_SEGMENT_LNS,*IMG_SEGMENT_DSC,
                   *IMG_SEGMENT_AUT,*IMG_SEGMENT_LOC,*IMG_SEGMENT_GPS,*IMG_SEGMENT_DATE]

    # Segments used for metadata
    
    # technical data, example
    # Make:SONY | Model:ILCE-6500 | LensMount:E-mount | LensModel:E 18-135mm F3.5-5.6 OSS |  ExposureTime:1/13 | ISO:250 
    # | Aperture:9.0 | FocalLength:31.0 mm | ScaleFactor35efl:1.5 | FocalLengthIn35mmFormat:46 mm |  FOV: 112.6 deg |
    # LensFormat:APS-C | CircleOfConfusion:0.020 mm | HyperfocalDistance:5.27 m |  LightValue:8.7 | 
    # FocusMode:AF-S  OriginatingProgram:None | 
    IMG_SEG_TECH_USED = ["Make","Model","LensMount","LensModel","LensInfo","ExposureTime","ISO","Aperture",
                         "FocalLength","ScaleFactor35efl","FocalLengthIn35mmFormat", "FOV","LensFormat","CircleOfConfusion",
                         "HyperfocalDistance","LightValue","ExposureCompensation","FocusMode","FocusDistance2","Software"]
    
    # Geo Data 
    IMG_SEG_GEO = [*IMG_SEGMENT_DATE,*IMG_SEGMENT_GPS,*IMG_SEGMENT_LOC]
    
    # Metadata that contain metadata in lists
    META_DATA_LIST = ['Keywords','HierarchicalSubject'] 

    # Mapping Reverse Geo Data To Metadata
    MAP_REVERSEGEO2META = { 'CountryPrimaryLocationName':'address_country',
                            'CountryPrimaryLocationCode':'address_country_code',
                            'ProvinceState':'address_state',
                            'ImageDescription':'properties_display_name',
                            'Caption-Abstract':'properties_display_name',
                            'City': ('address_city','address_town','address_village'),
                            'Sublocation': ('properties_name','address_tourism','address_historic',
                                            'address_isolated_dwelling','address_hamlet',
                                            'address_suburb','address_road'),
                            'SpecialInstructions':'url_geohack' }
    
    # metadata hierarchy for geo data
    META_HIER_GEO = ('CountryPrimaryLocationName','ProvinceState','City','Sublocation') 

    # metadata short description fields
    META_DESC = ('ObjectName','Title','Headline','CaptionAbstract') 

    # EXIFTOOL command line parameters, refer to
    # https://exiftool.org/exiftool_pod.html
    # j: json format G:Group names c ,'%+.6f' Geo Coordinates in decimal format 
    EXIF_AS_JSON = ('-j','-G','-s','-c','%+.8f')
    # same but short version without segments
    EXIF_AS_JSON_SHORT = ('-j','-s','-c','%+.8f')
    
    # -output as command/arg file -args -charset UTF8 -s test.jpg
    # -args arg format character set -s short format
    EXIF_AS_ARG = ('-args','-s','-c','%+.8f')

    # -write metadata from command tool
    # -m ignore minor issues -sep ", " / use "comma space" as separator for lists eg tags; 
    # @ <argsfile> use this command file 
    # -m -sep ", '-c' '%+.8f' " -charset UTF8 @ <argsfile> test.jpg
    EXIF_ARG_WRITE = ('-m','-sep',EXIF_LIST_SEP,'-c','%+.8f')

    def __init__(self, executable,debug=False):
        if not ( os.path.isfile(executable) and "exiftool" in executable.lower() ):
            print("executable is not exiftool, exiting ...")
            return None            
        self.executable = executable
        self.debug = debug

    def __enter__(self):   
        self.process = subprocess.Popen(
            [self.executable, "-stay_open", "True",  "-@", "-"],
            universal_newlines=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self

    def  __exit__(self, exc_type, exc_value, traceback):
        self.process.stdin.write("-stay_open\nFalse\n")
        self.process.stdin.flush()

    def execute(self, *args):
        """ receives command line params to be used for exif tool, for options see
             Options used are defined as constants here """
        args = args + ("-execute\n",)
        if self.debug is True:
            print("EXECUTE:",args)
        self.process.stdin.write(str.join("\n", args))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.endswith(self.SENTINEL):   
            output += os.read(fd, 4096).decode('utf-8')
        return output[:-len(ExifTool.SENTINEL)]

    def get_metadict_from_img(self,filenames,metafilter=None,filetypes=IMG_FILE_TYPES,list_metadata=META_DATA_LIST,charset="UTF8") -> dict:
        """ reads EXIF data in args format into dictionary, with the filter list only selected metadata will be read """

        meta_arg_dict = {}
        if not metafilter is None: 
            metafilter = ["Directory","FileName",*metafilter]

        fileref = Persistence.get_file_list(path=filenames,file_type_filter=filetypes)

        if isinstance(fileref, str):
            fileref = [fileref]

        arg_list = list(self.EXIF_AS_ARG)
        arg_list = [*arg_list,'-charset',charset]

        for f in fileref:
            arg_dict = {}

            try:
                args = self.execute(*arg_list,f).split(self.NEW_LINE)
            except:
                print(f"Exception with file {f}, exiftool params {arg_list} processing will be skipped")
                print(traceback.format_exc())
                continue

            for arg in args:
                l = len(arg)
                if l <= 2:
                    continue
                idx = arg.find("=")
                meta_key = arg[1:idx]
                if metafilter is not None:
                    if not ( meta_key in metafilter ):        
                        continue
                meta_value = arg[idx+1:l]

                # values contains a list
                if ( meta_key in list_metadata ) : 
                    meta_value = meta_value.split(ExifTool.EXIF_LIST_SEP)
                
                arg_dict[meta_key] = meta_value
                
            file_dir = arg_dict.get("Directory",None)
            file_name = arg_dict.get("FileName",None)

#           get path and filename from fileref
            if file_dir is None or file_name is None:
                filepath_info = Persistence.get_filepath_info(filepath=f)
                file_dir = filepath_info["parent"]
                file_name = f[(len(file_dir)+1):]                

            file_path = os.path.normpath(os.path.join(file_dir,file_name))
            meta_arg_dict[file_path] = arg_dict    
        
        return meta_arg_dict
    
    @staticmethod
    def write_args_from_dict(path,append_data=False,meta_values:dict=None,metafilter=None,add_digest=False,delete=False,charset="UTF8",debug=False):
        """ writes arguments file with given metadata dictionary
            path: file path to new args file
            append_data: Flag if any existing file should be overwritten or blended with data
            meta_values: data to be written to args file
            metafilter: only keys matching to list in metafilter will be written (None=all data)
            add_digest: digest value to be written to args file
        """
        
        # gets the file list
        #img_list = Persistence.get_file_list(path=path,file_type_filter=filetypes)
        
        # reads arg metadata from image file as meta data dictionary
        #meta_args = self.get_metadict_from_img(img_list)
        #args_files = []
        
        #for f,meta in meta_args.items():
            # construct new args filename

        p = Path(path)
        parent = p.parent
        name = p.stem + "." + ExifTool.ARGS
        args_filename = os.path.normpath(os.path.join(parent,name))

        meta = {} 
        
        # # overwrite meta values
        if not meta_values is None:
            for k,v in meta_values.items():
                meta[k] = v
        
        # filter list for writing
        if metafilter is None:
            meta_filter_keys = meta.keys()
        else:
            metafilter = list(metafilter)
            meta_filter_keys = list(filter(lambda li: li in metafilter, meta.keys()))     

        if debug is True:
            print("---------------------------------")
            print("Metadata args File:",args_filename)
            print("Template Dict:",meta)         
            print("Filter",metafilter,"Filtered keys",meta_filter_keys)

        # Add IPTCdigest
        if add_digest is True:
            meta["IPTCDigest"] = "new"
            if not metafilter is None:
                metafilter.append("IPTCDigest")

        # filter list for writing
        if metafilter is None:
            meta_filter_keys = meta.keys()
        else:
            meta_filter_keys = list(filter(lambda li: li in metafilter, meta.keys()))
            if debug is True:
                print("META",meta_filter_keys)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        s = f"# ----- Metadata {args_filename} ------\n"
        s += f"#       from {timestamp} \n"
        s += ExifTool.dict2arg(meta_dict=meta,filter_list=meta_filter_keys,delete=delete)
        
        msg = Persistence.save_file(s,args_filename,append_data=append_data)
        
        if debug is True:
            print(f"Writing {args_filename}") 
            print("Number of keys to write:",len(meta_filter_keys)) 
            print("Args File (...) :\n",s[:min(500,len(s))])
            print(msg)
            
        # return path
        return args_filename


    def write_args_from_img(self,path,append_data=False,meta_values:dict=None,metafilter=None,delete=False,add_digest=False,filetypes=["jpg","jpeg"],charset="UTF8"):
        """ writes arguments files with given metadata dictionary for each jpg file in given directory path
            (or in case path is a path to a single image then only this image will be processed )
            per default, all metadata is written into the files (with the exception of file information)
            meta_values dictionary allows to change / overwrite metadata values that are otherwise read from file
            submitting metadata filter (=list of metadata attributes) will only write filtered attributes
            append_data allows metadata to be added to existing args files
            delete controls whether data are to be deleted from image file
            returns list of creared args files
        """

        if not metafilter is None:
            metafilter = list(metafilter)
        
        # gets the file list
        img_list = Persistence.get_file_list(path=path,file_type_filter=filetypes)
        
        # reads arg metadata from image file as meta data dictionary
        meta_args = self.get_metadict_from_img(img_list)
        args_files = []
        
        for f,meta in meta_args.items():
            # construct new args filename
            p = Path(f)
            parent = p.parent
            name = p.stem + "." + self.ARGS
            args_filename = os.path.normpath(os.path.join(parent,name))

            if self.debug is True:
                print("---------------------------------")
                print("Metadata args File:",args_filename," Number of metadata entries:",len(meta.keys()))          
            
            # overwrite meta values
            if not meta_values is None:
                for k,v in meta_values.items():
                    meta[k] = v

            # Add IPTCdigest
            if add_digest is True:
                meta["IPTCDigest"] = "new"
                if not metafilter is None:
                    metafilter.append("IPTCDigest")
            
            # delete filename / path
            meta.pop("FileName",None)
            meta.pop("Directory",None)

            # filter list for writing
            if metafilter is None:
                meta_filter_keys = meta.keys()
            else:
                meta_filter_keys = list(filter(lambda li: li in metafilter, meta.keys()))
                if self.debug is True:
                    print("META",meta_filter_keys)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            s = f"# ----- Metadata {f} ------\n"
            s += f"#       from {timestamp} \n"
            s += self.dict2arg(meta_dict=meta,filter_list=meta_filter_keys,delete=delete)
            
            msg = Persistence.save_file(s,args_filename,append_data=append_data)
            args_files.append(args_filename)
            
            if self.debug is True:
                print(f"Writing {args_filename}") 
                print("Number of keys to write:",len(meta_filter_keys)) 
                print("Args File (...) :\n",s[:min(500,len(s))])
                print(msg)
            
        return args_files

    def write_args2img(self,path,filetypes=["jpg","jpeg"],charset="UTF8",show_info=False) -> None:
        """ writes metadata from args file into image files in a given directory path with extension jpg
            args file needs to have the same name as the corresponding image name 
            (test.jpg requires a test.args file )  
        """

        # writing params
        args_list_raw = [*self.EXIF_ARG_WRITE,'-charset',charset,'-@']
        arg_files = []

        if os.path.isfile(path):
            # single image file
            for ty in filetypes:
                arg_file = path.replace(ty,"args")
                if arg_file != path:
                    arg_files = [arg_file]
        else:
            # get all arg files in path
            arg_files = Persistence.get_file_list(path=path,file_type_filter="args")

        print("ARG FILES",arg_files)

        if show_info is True:
            print(f"WRITE IMAGE METADAT: EXIFTOOL ARGS {args_list_raw}")
            print(f"Arg File List # files ({len(arg_files)}): {str(arg_files)[:300]} ... \nWRITING -> ",end="")   

        # for each arg file get the corresponding image file
        for arg_file in arg_files:
            p = Path(arg_file)
            parent = p.parent
            stem = p.stem + "."
            for f in filetypes:
                img_path = os.path.join(parent,stem+f)
                if os.path.isfile(img_path):
                    args_list = [*args_list_raw,arg_file]
                    self.execute(*args_list,img_path)
                    if show_info is True:
                        print(f".", end = "")
        
        if show_info is True:
            print("\nWRITING IS FINISHED!")
        
        return None

    @staticmethod
    def arg2dict(args:list,filter_list:list=None,delete:bool=False)->dict:
        """ converts arg value list into value dict 
            filter list to export only selected keys can also be applied
            if delete set to true, the values will be initialized (=deleted)
        """    
        args_dict = {}
        for arg in args:
            if not ( arg[0] == "-" ):
                continue
            key_raw,value_raw = arg.strip().split("=")
            key = key_raw[1:len(key_raw)]
            
            if ( key in ExifTool.META_DATA_LIST ):
                value = value_raw.split(ExifTool.EXIF_LIST_SEP)
            else:
                value = value_raw

            if delete is True:
                value = ""

            if ( filter_list is None ):                
                args_dict[key] = value
            else:
                if key in filter_list:
                    args_dict[key] = value
        
        return args_dict
        
    @staticmethod
    def dict2arg(meta_dict:dict,filter_list:list=None,delete:bool=False)->str:
        """ converts key value dict into arg file string 
            filter list to export only selected keys can also be applied
            if delete set to true, the values will be initialized (=deleted)
        """
        s = ""

        keys = []

        if filter_list is None:
            keys = meta_dict.keys()
        else:
            expr = lambda x: True if x in filter_list else False
            keys = list(filter(expr,meta_dict.keys()))     

        for k in keys:
            v = meta_dict[k]
            if isinstance(v,list):
                v = ExifTool.EXIF_LIST_SEP.join(v)

            if delete is False:
                s += ''.join(['-',str(k),'=',str(v),'\n'])
            else:
                s += ''.join(['-',str(k),'=\n'])

        return s

    def get_metadict_from_img2(self, path,file_type_filter=['jpg','jpeg']) -> dict:
        """ reads EXIF data from a single file or a file list
            as filenames path as string is alllowed or a list of path strings 
            returns metadata as dictionary with filename as key """
            
        fileref = Persistence.get_file_list(path=path,file_type_filter=file_type_filter)

        if self.debug is True:
            print("[ExifTool] Files to be processed "+str(fileref))

        meta_data_list_raw = json.loads(self.execute(*self.EXIF_AS_JSON_SHORT,*fileref))
        meta_data_list = {}
        for meta_data in meta_data_list_raw:
            file_name = meta_data.pop("SourceFile",None)
            meta_data_list[file_name] = meta_data

        return meta_data_list
    
    @staticmethod
    def get_tech_keywords_from_metadict(metadict:dict,debug=False) -> list:
        """ gets technical keywords from metadata dictionary """

        def zip_str(s):
            return "".join(s.split(" "))
        
        tech_params_out = []
        
        if debug is True:
            print("--- get_tech_keywords_from_metadict---\n")
            print(metadict)

        # get make model and mount
        lens_format = metadict.get("LensFormat","")
        if not ( lens_format == '' or lens_format == 'Unknown' ):
            lens_format = "("+lens_format+")"
        else:
            lens_format = ''
        tech_params_out.append((" ".join(["CAM",metadict.get("Make",""),metadict.get("Model",""),lens_format])).strip())    

        # get lens focal length aperture and ISO
        lens = metadict.get("LensModel","")
        if lens == "":
            lens = metadict.get("LensInfo","")
        elif lens == "----":
            lens = "MANUAL"
        tech_params_out.append(("LENS "+lens))

        fl = zip_str(metadict.get("FocalLength","N/A"))
        if fl[0:3] == "0.0":
            fl = ""
        else:
            fl = "f"+fl
        ap = metadict.get("Aperture","NA")
        if ap == "NA":
            ap = ""
        else:
            ap = " F"+ap

        s = fl+ap
        s += " T"+metadict.get("ExposureTime","N/A")+"s"
        s += " ISO"+metadict.get("ISO","N/A")
        s = s.strip()
        tech_params_out.append(s)

        # get 35mm equivalents
        if lens != "MANUAL":
            s = "f(35mm) "+zip_str(metadict.get("FocalLengthIn35mmFormat","N/A"))
            s += " ("+metadict.get("ScaleFactor35efl","N/A")+")"
            tech_params_out.append(s)
        
        # photonerd params :-)
        coc = metadict.get("CircleOfConfusion")
        if not coc is None:
            coc_nm = coc.split(" ")[0]
            try:
                coc_nm = "coc "+str(int(1000*float(coc_nm)))+"nm"
                tech_params_out.append(coc_nm)
            except:
                pass
                
        foc = metadict.get("FocusDistance2","")  
        if not foc == "":
            foc = "focus dist. "+zip_str(foc)    
            tech_params_out.append(foc)
            
        hfoc = metadict.get("HyperfocalDistance","")       
        if not hfoc == "":
            hfoc = "hyperfocal "+zip_str(hfoc)    
            tech_params_out.append(hfoc)
                
        fov = metadict.get("FOV","")
        if not fov == "":
            fov = "fov "+zip_str(fov)
            tech_params_out.append(fov)
        
        ev = metadict.get("LightValue","")
        if not ev == "":
            ev= "Light "+ev+"EV"
            tech_params_out.append(ev)
                
        
        focus = metadict.get("FocusMode","")
        if not focus == "":
            focus= "focus "+focus
            tech_params_out.append(focus)
        
        # clean out empty elements
        tech_params_out = list(filter(lambda v:v!="",tech_params_out))
        if debug is True:
            print("OUT PARAMS \n",tech_params_out)    
        
        return tech_params_out    

    @staticmethod
    def get_gps_keywords_from_gpx(metadict:dict,gpx_dict:dict,gpx_keys:list=None,
                                  time_offset=0,timeframe=60,debug=False) -> dict:
        """ reads gpx tracklog data and tries to match with image timestamp 
            time offset will be added to camera timestamp to correlate with gps time 
            gpx_keys is the sorted list of gpx_dict_keys / timestamps (should be done before)
            gps_timeframe is acceptable time stamp difference whether data are considered to be matching 
            (60 seconds is set)
            """
        gps_dict = {}

        if gpx_keys is None:
            gpx_keys = sorted(list(gpx_dict.keys()))
        
        # get datetime and timestamp 
        d = metadict.get("CreateDate",0)
        d_ts = Util.get_timestamp(d) + time_offset
        
        # will return -1 if index is out of bounds
        gpx_idx = Util.get_nearby_index(d_ts,gpx_keys,debug=False)
        if ( gpx_idx == -1 ):
            return gps_dict
        d_ts_gpx  = gpx_keys[gpx_idx]       
        delta_ts = abs(d_ts_gpx-d_ts)
        
        if debug is True:
            print(f"GET GPS: Date Image {d} Timestamp {d_ts} GPX Timestamp {d_ts_gpx} Difference {delta_ts} sec")
        
        if ( delta_ts > timeframe ):
            return gps_dict
        
        # gps from gpx file
        gpx_lat = gpx_dict[d_ts_gpx]["lat"]
        gpx_lon = gpx_dict[d_ts_gpx]["lon"]
        gpx_alt = gpx_dict[d_ts_gpx]["ele"]
        latlon_gpx = (gpx_lat,gpx_lon)
        
        if debug is True:
            # existing gps data 
            img_lat = float(metadict.get("GPSLatitude",999))
            img_lon = float(metadict.get("GPSLongitude",999))
            img_alt = float(metadict.get("GPSAltitude","999 m").split()[0])

            # gps data in image already
            if ( img_lat == 999 or img_lon == 999 ):
                print("No GPS data on Image")
            else:
                latlon_img = (img_lat,img_lon)           
                print(f"GPS lat lon alt from gpx: {latlon_gpx,gpx_alt}")
                print(f"GPS lat lon alt from img: {latlon_img,img_alt}")
                geo_diff = round(1000 * Geo.get_distance(latlon_gpx,latlon_img),1)
                print(f"Difference GPS vs. Image {geo_diff} meters")            
        
        gps_dict = Geo.get_exifmeta_from_latlon(latlon=latlon_gpx,altitude=gpx_alt,timestamp=d_ts_gpx)

        return gps_dict

    @staticmethod
    def create_metahierarchy_from_str(meta_hierarchy_raw:list,debug=False) -> dict:
        """ Creates hierarchical meta data from raw string format (1 tab = 1 level) 
            Example
            m1
                m1.1
                m1.2
            m2
                m2.1
                    m2.1.1
            will create the following hierarchical metadata tags as dict 
            ["m1|m1.1","m1|m1.2","m2|m2.1|m2.1.1"]
        """ 
        hier_tag_dict = {}
        hier_meta_dict = {}
        sep = ExifTool.HIER_SEP
        for meta_raw in meta_hierarchy_raw:
            level_current = meta_raw.count("\t")
            tag = meta_raw.replace("\t","").strip()
            hier_tag = ""
            hier_meta_dict[level_current] = tag   
            max_level = max(hier_meta_dict.keys())   
            del_range = range(level_current+1,max_level+1)  
            [hier_meta_dict.pop(m) for m in del_range] 
            hier_tag_list = [hier_meta_dict[m] for m in range(level_current)]     
            hier_tag_list.append(tag)
            hier_tag = sep.join(hier_tag_list)
            if debug is True:
                print(f"Level:",level_current,"(",tag,") -> ",hier_tag)
            hier_tag_dict[tag] = hier_tag

        return hier_tag_dict
    
    @staticmethod
    def get_keywords(meta_dict:dict,new_keys:list,overwrite=False):
        """ add new keys to Keywords list, overwrite overwrites existing keywords """
        
        if overwrite is False:
            keyword_list = meta_dict.get("Keywords",[])
        else:
            keyword_list = []
        
        keyword_list =  list(dict.fromkeys([*keyword_list,*new_keys]))
        
        return keyword_list
    
    @staticmethod
    def get_hier_subject(meta_dict:dict,hier_dict:dict={},overwrite=False):
        """ add new keys to Hierarchival subject list, overwrite overwrites existing keywords """
        if overwrite is False:
            keyword_list = meta_dict.get("HierarchicalSubject",[])
        else:
            keyword_list = []
        
        keywords = meta_dict.get("Keywords",[])
        hier_keys = filter(lambda l:(l is not None),map(lambda k:hier_dict.get(k),keywords))
        keyword_list = list(dict.fromkeys([*keyword_list,*hier_keys]))
        
        return keyword_list
    
    @staticmethod
    def path2title(path,debug=False):
        """ gets the parent path. if it conforms to the format YYYYMMDD_X_<TITLE_OTHERS> the last part
            will be extracted. A path to a file also can be submitted. Path needs to point to a real path or file 
        """
        pf = Path(path)

        subfolder = ""
        #get either parent path of file or last folder 
        if os.path.isfile(pf):
            subfolder = pf.parts[-2]
        elif os.path.isdir(pf):
            subfolder = pf.parts[-1]

        subfolder_elems = subfolder.split("_")

        #at least three elements must be given
        if len(subfolder_elems) >= 3:
            title = " ".join(subfolder_elems[2:])
        else:
            print(f"{path} is not a path or a folder / doesnt contain _ as separator")
            title = ""
        
        if debug is True:
            print(f"Path: {path}, Title is {title}")

        return title
    
    @staticmethod
    def get_author_dict(author:str):
        """ returns metadata attributes for author """   
        author_dict = {}      
        copyright = f"{ExifTool.COPYRIGHT} {datetime.now().strftime('%Y')} {author}"
        author_dict['WriterEditor'] = author
        author_dict['Copyright'] = copyright
        author_dict['CopyrightNotice'] = "All Rights Reserved"
        author_dict['Credit'] = author
        author_dict['Source'] = "Photo made by Author"

        return author_dict
    
    @staticmethod
    def get_title_dict(title:str):
        """ returns metadata attributes for title / descriptions """
        meta_list = ['ObjectName','Title','Label','ImageDescription','Caption-Abstract','Description','Headline']
        title_dict = {}      
        [title_dict.update({d:title}) for d in meta_list]
        return title_dict
    
    @staticmethod
    def map_geo2exif(geo_dict:dict,debug=False)->dict:
        """ maps geo data to exif metadata """

        meta = {}

        # map metadata - reverse key dict
        for meta_key,reverse_key in ExifTool.MAP_REVERSEGEO2META.items():
            v = None
            if isinstance(reverse_key,tuple):
                for k in reverse_key:
                    v = geo_dict.get(k,None)
                    if v is not None:
                        break
            else:
                v = geo_dict.get(reverse_key,None)
            if v is not None:
                meta[meta_key] = v

        # process metadata / metadata hierarchy
        keywords = []
        hier_key = ""
        for key in ExifTool.META_HIER_GEO:
            value =  meta.get(key,None)
            if value is not None:
                keywords.append(value)

        meta['Keywords'] = keywords

        if keywords:
            hier_key = ExifTool.HIER_SEP.join(keywords)
        
        meta['HierarchicalSubject'] = hier_key

        # map geo meta data to description fields
        title = None
        city = meta.get('City',None)
        subloc = meta.get('Sublocation',None)
        if city is not None:
            title = city
        if subloc is not None:
            title = title + " (" + subloc + ")"
        if title is not None:
            for d in ExifTool.META_DESC:
                meta[d] = title
        
        if debug:
            print("  ---- Exiftool.map_geo2exif ----")
            Util.print_dict_info(meta)

        return meta


