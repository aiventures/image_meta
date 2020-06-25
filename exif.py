""" module to handle exif data (with EXIF Tool) """

import subprocess
import os
import json

class ExifTool(object):
    """ Interface to EXIF TOOL"""

    SENTINEL = "{ready}\r\n"
    SEPARATOR = "\\" 
    NEW_LINE = "\r\n"

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

    # EXIFTOOL command line parameters, refer to
    # https://exiftool.org/exiftool_pod.html
    # j: json format G:Group names c ,'%+.6f' Geo Coordinates in decimal format 
    EXIF_AS_JSON = ('-j','-G','-s','-c','%+.8f')
    # -output as command/arg file -args -charset UTF8 -s test.jpg
    # -args arg format character set -s short format
    EXIF_AS_ARG = ('-args','-s','-c','%+.8f')

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
        self.process.stdin.write(str.join("\n", args))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.endswith(self.SENTINEL):   
            output += os.read(fd, 4096).decode('utf-8')
        return output[:-len(ExifTool.SENTINEL)]

    def get_meta_args(self,filenames,charset="UTF8") -> dict:
        """ reads EXIF data in args format into dictionary """

        meta_arg_dict = {}
        fileref = filenames
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
                meta_value = arg[idx+1:l]
                arg_dict[meta_key] = meta_value
            file_dir = arg_dict.pop("Directory",None)
            file_name = arg_dict.pop("FileName",None)
            file_path = os.path.join(file_dir,file_name).replace("/",self.SEPARATOR)
            meta_arg_dict[file_path] = arg_dict    
        
        return meta_arg_dict

    def get_metadata(self, filenames) -> dict:
        """ reads EXIF data from a single file or a file list
            as filenames path as string is alllowed or a list of path strings 
            returns metadata as dictionary with filename as key """
            
        if self.debug is True:
            print("[ExifTool] Files to be processed "+str(filenames))
        
        fileref = filenames
        if isinstance(fileref, str):
            fileref = [fileref]

        meta_data_list_raw = json.loads(self.execute(*self.EXIF_AS_JSON,*fileref))
        meta_data_list = {}
        for meta_data in meta_data_list_raw:
            file_name = meta_data.pop("SourceFile",None)
            meta_data_list[file_name] = meta_data

        return meta_data_list
    
    @staticmethod
    def create_meta_hierarchy_tags(meta_hierarchy_raw:list,debug=False) -> dict:
        """ Creates hierarchical meta data from raw file (1 tab = 1 level) 
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

    
    # def write_metadata(self):
    #     file_name = file_dir + self.SEPARATOR + r"1.jpg"
    #     file_list = [file_name]
    #     print(file_name)
    #     #write keywords        
    #     self.execute("-keywords=Frankx","-keywords=Und x noch einer", *file_list)  
    #     self.execute("-xmp:subject<$iptc:keywords",*file_list)
    #     #copy to exif
    #     #check metadata
    #     #meta_data = json.loads(self.execute('-j','-G','-keywords',*file_list))
    #     #meta_data = json.loads(self.execute('-j','-G',''*filenames))
    #     meta_data = self.get_metadata(file_name)        
    #     return meta_data