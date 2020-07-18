import re
from datetime import datetime
from datetime import timedelta

import pytz

class Util:
    """ util module """

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
                #dt = datetime.strptime(dt_s,"%Y-%m-%d %H-%M-%S").replace(tzinfo=timezone_loc)
                dt = datetime.strptime(dt_s,"%Y-%m-%d %H-%M-%S")
                dt = timezone_loc.localize(dt)
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