""" module to handle exif data (with EXIF Tool) """

import subprocess
import os
import json

# test
class ExifTool(object):
    """ Interface to EXIF TOOL"""
    SENTINEL = "{ready}\r\n"
    SEPARATOR = "\\" 

    # EXIFTOOL command line parameters, refer to
    # https://exiftool.org/exiftool_pod.html
    # j: json format G:Group names c ,'%+.6f' Geo Coordinates in decimal format 
    EXIF_AS_JSON = ('-j','-G','-c','%+.6f')

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

    def get_metadata(self, filenames):
        """ reads EXIF data from a single file or a file list
            as filenames path as string is alllowed or a list of path strings 
            returns metadata as dictionary with filename as key """
            
        if self.debug is True:
            print("[ExifTool] Files to be processed "+filenames)
        
        fileref = filenames
        if isinstance(fileref, str):
            fileref = [fileref]

        meta_data_list_raw = json.loads(self.execute(*self.EXIF_AS_JSON,*fileref))
        meta_data_list = {}
        for meta_data in meta_data_list_raw:
            file_name = meta_data.pop("SourceFile",None)
            meta_data_list[file_name] = meta_data

        return meta_data_list
    
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