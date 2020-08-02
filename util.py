import re
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from dateutil.tz import tzutc
from dateutil.tz import tzoffset
import pytz

class Util:
    """ util module """

    NOT_FOUND = -1

    @staticmethod
    def get_datetime_from_string(datetime_s:str,local_tz='Europe/Berlin',debug=False) -> str:
        """ returns datetime for date string with timezone 
            allowed formats:  ####:##:## ##:##:##  (datetime localized with local_tz) 
                              ####-##-##T##:##:##Z  (UTC) 
                              ####-##-##T##:##:##.000Z
                              ####-##-##T##:##:##(+/-)##:## (UTC TIme Zone Offsets)
                            
            (<year>-<month>-<day>T<hour>-<minute>(T/<+/-time offset)    
        """    
        dt = None

        if debug is True:
            datetime_s_in = datetime_s[:]

        reg_expr_utc = "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"
        reg_expr_dt = "\\d{4}[:-]\\d{2}[:-]\\d{2} \\d{2}[:-]\\d{2}[:-]\\d{2}"

        reg_expr_utc2 = "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}[.]000Z$"
        reg_expr_tz = "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}[+-]\\d{2}:\\d{2}$"
        
        if ( ( len(re.findall(reg_expr_dt, datetime_s)) == 1 ) ): # date time format
            try:
                timezone_loc = pytz.timezone(local_tz)
                dt_s = datetime_s[0:4]+"-"+datetime_s[5:7]+"-"+datetime_s[8:10]+" "+datetime_s[11:13]+"-"+datetime_s[14:16]+"-"+datetime_s[17:19]
                dt = datetime.strptime(dt_s,"%Y-%m-%d %H-%M-%S")
                dt = timezone_loc.localize(dt) # abstain from datetime.replace :-) ...
            except:
                return 0

        elif  ( len(re.findall(reg_expr_utc2, datetime_s)) == 1 ): # utc2 format
            datetime_s = datetime_s[:-5] + "+00:00" 
        elif ( len(re.findall(reg_expr_utc, datetime_s)) == 1 ): # utc format
            datetime_s = datetime_s[:-1] + "+00:00" 
        elif ( len(re.findall(reg_expr_tz, datetime_s)) == 1 ): # time zone format  
            pass # this time zone already has the correct format
        else:
            print(f"can't evaluate time format {datetime_s} ")
            return 0
        
        if dt is None:
            # omit colon
            try:
                dt_s = datetime_s[:-3]+datetime_s[-2:]
                dt = datetime.strptime(dt_s, "%Y-%m-%dT%H:%M:%S%z")
            except:
                return None
        
        if debug is True:
            print(f"IN:{datetime_s_in}, dt:{dt}, tz:{dt.tzinfo} utc:{dt.utcoffset()}, dst:{dt.tzinfo.dst(dt)}")    

        return dt              


    @staticmethod
    def get_timestamp(datetime_s:str,local_tz='Europe/Berlin',debug=False) -> int:
        """ returns UTC timestamp for date string  
        """

        dt = Util.get_datetime_from_string(datetime_s,local_tz,debug)
        ts = int(dt.timestamp())
        if debug is True:
            print(f"Datestring: {datetime_s} Timezone {local_tz} Timestamp: {ts}")
        
        return ts

    @staticmethod
    def get_time_offset(time_camera:str,time_gps:str,debug=False)->timedelta:
        """ helps to calculate offset due to difference of GPS and Camera Time Difference
            difference = time(gps) - time(camera) > time(gps) = time(camera) + difference
            returns a timedelta object
        """
        try:
            ts_gps = datetime.fromtimestamp(Util.get_timestamp(time_gps,debug=debug))
            ts_cam = datetime.fromtimestamp(Util.get_timestamp(time_camera,debug=debug))
        except:
            raise Exception(f"GPS Timestamp {time_gps} or Camera Timestamp {time_camera} not correct") 

        delta_time = ts_gps - ts_cam

        if debug is True:
            print(f"Camera:{time_camera} GPS:{time_gps} Time Offset:{(delta_time//timedelta(seconds=1))}")

        return delta_time        

    @staticmethod
    def get_localized_datetime(dt_in,tz_in="Europe/Berlin",tz_out="UTC",as_timestamp=False,debug=False):
        """helper method to get non naive datetime (based on input and output timezone), 
           input date can be string or datetime,
           timezone can be string or pytz object, optionally returns also as utc timestamp"""
        
        reg_expr_datetime = "\\d{4}[-:]\\d{2}[:-]\\d{2} \\d{2}[:-]\\d{2}[:-]\\d{2}"       
        
        def get_tz_info(tz):
            if isinstance(tz,pytz.BaseTzInfo):
                tz_info = tz
            elif isinstance(tz_in,str):
                tz_info = pytz.timezone(tz)
            else:
                tz_info = pytz.timezone("UTC")
            return tz_info
        
        tz_utc = pytz.timezone("UTC")
        pytz_in = get_tz_info(tz_in)
        pytz_out = get_tz_info(tz_out)

        if isinstance(dt_in,datetime):
            dt = dt_in
        elif isinstance(dt_in,str):
            # convert date hyphens
            if (len(re.findall(reg_expr_datetime, dt_in))==1):
                dt_in = (dt_in[:10].replace(":","-")+dt_in[10:])
            
            # utc code
            if dt_in[-1] == "Z":
                dt_in = dt_in[:-1]+"+00:00"
            dt = parse(dt_in)
        
        tz_info = dt.tzinfo
        
        # naive datetime, convert to input timezone
        if tz_info is None:
            dt = pytz_in.localize(dt)
            tz_info = dt.tzinfo

        # convert to utc time formats
        if (isinstance(tz_info,tzutc)) or (isinstance(tz_info,tzoffset)):
            dt_utc = dt.astimezone(tz_utc)
        else:
            dt_utc = tz_utc.normalize(dt)
        
        # convert to target timezone
        if as_timestamp:
            out = dt_utc.timestamp()
        else:
            out = dt_utc.astimezone(pytz_out)
        
        if debug is True:
            print(f"date IN: {dt_in} -> datetime {dt} ({pytz_in})")
            print(f"  -> UTC datetime {dt_utc} -> datetime {out} ({pytz_out})")
            ts = dt_utc.timestamp()
            print(f"  -> Timestamp {ts} with UTC datetime {datetime.utcfromtimestamp(ts)}")        
        return out
            

    @staticmethod
    def get_nearby_index(value,sorted_list:list,debug=False):
        """ returns index for closest value in a sorted list for a given input value,
            uses binary search
        """
        
        idx = -1
        idx_min = 0
        idx_max = len(sorted_list)
        idx_old = -2
        
        finished = False

        if debug is True:
            print("List: ",sorted_list)    
        
        # out of bounds will return a negative value
        if ( ( sorted_list[idx_max-1] < value ) or ( sorted_list[0] > value ) ) :            
            finished = True
        
        while not finished:
            idx = idx_min + ( idx_max - idx_min ) // 2
            
            # converged / exact value not found
            if ( idx == idx_old ):
                finished = True
            
            val_idx = sorted_list[idx]        
            if ( val_idx < value ):
                idx_min = idx
            elif ( val_idx > value ):
                idx_max = idx
            else:
                finished = True
                
            idx_old = idx
            
            if debug is True:
                print("List: ",sorted_list[idx_min:idx_max])    
        return idx
    
    @staticmethod
    def print_dict_info(d:dict,s="",show_info=True,list_elems=9999,verbose=True):
        """ prints information in dictionary """
        
        if not show_info:
            return

        if s != "":
            print(f"--- Dictionary Content {s} ---")

        for k,v in d.items():
            s = ""
            n = 0
            if isinstance(v,list):
                n = min(len(v),list_elems)
                print(f"Element {k} has list with {len(v)} elements, showing {n} elements")                
                print(f"   {k}  ->  {v[:n]}")
            elif isinstance(v,dict):
                n = min(len(v.keys()),list_elems)
                print(f"Element {k} has dictionary with {len(v.keys())} attributes, showing {n} attributes")
                d_keys = list(v.keys())[:n]
                s = f"   {k}  ->  "
                for d_key in d_keys:
                    s += f"\n   {d_key}:{v[d_key]}"
                print(s)
            else:
                print(f"   {k}  ->   {v}")
