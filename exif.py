""" module to handle exif data (with EXIF Tool) """

import subprocess
import os
import json
from datetime import datetime
from image_meta.persistence import Persistence
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

    SENTINEL = "{ready}\r\n"
    SEPARATOR = os.sep
    EXIF_LIST_SEP = ", "
    NEW_LINE = "\r\n"
    ARGS = "args"
    COPYRIGHT = u'©'

    # relevant metadata definitions (for specification check  https://www.iptc.org/std/photometadata/documentation/) 
    
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
    IMG_SEGMENT_DSC = ['CurrentIPTCDigest', 'IPTCDigest', 'CodedCharacterSet', 'Subject', 'Keywords', 
                       'HierarchicalSubject', 'ObjectName', 'UserComment', 'Byline', 'Headline', 
                       'BylineTitle', 'Artist', 'ImageDescription', 'CaptionAbstract', 'Category']
    # Author
    IMG_SEGMENT_AUT = ['WriterEditor', 'Copyright', 'CopyrightNotice', 'Credit','CopyrightFlag', 'Source', 
                       'EditStatus', 'FixtureIdentifier', 'SpecialInstructions',  'OriginalTransmissionReference']
    # Location
    IMG_SEGMENT_LOC = ['City', 'Sublocation', 'ProvinceState', 'CountryPrimaryLocationCode', 'CountryPrimaryLocationName'] 
    # GPS 
    IMG_SEGMENT_GPS = ['GPSVersionID', 'GPSLatitudeRef', 'GPSLongitudeRef', 'GPSAltitudeRef', 'GPSTimeStamp', 'GPSMapDatum', 
                       'GPSDateStamp', 'GPSAltitude', 'GPSDateTime', 'GPSLatitude', 'GPSLongitude', 'GPSPosition']
    # Date 
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

    def get_metadict_from_img(self,filenames,metafilter=None,filetypes=["jpg","jpeg"],list_metadata=META_DATA_LIST,charset="UTF8") -> dict:
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
            args = self.execute(*arg_list,f).split(self.NEW_LINE)

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
            file_path = os.path.normpath(os.path.join(file_dir,file_name))
            meta_arg_dict[file_path] = arg_dict    
        
        return meta_arg_dict
    

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

        # get all arg files
        arg_files = Persistence.get_file_list(path=path,file_type_filter="args")

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
            key_raw,value_raw = arg.strip().split("=")
            key = key_raw[1:len(key_raw)]
            value = value_raw.split(ExifTool.EXIF_LIST_SEP)

            if len(value) == 1:
                value = value[0]

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
                s += ''.join(['-',k,'=',v,'\n'])
            else:
                s += ''.join(['-',k,'=\n'])

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
        sep = "|"  
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
