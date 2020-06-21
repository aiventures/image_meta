import re
from datetime import datetime
import pytz

class Util:
    """ util module """

    @staticmethod
    def get_timestamp(datetime_s:str,local_tz='Europe/Berlin',debug=False) -> int:
        """ returns UTC timestamp for date string 
            allowed formats:  ####:##:## ##:##:##  (datetime localized with local_tz) 
                              ####-##-##T##:##:##Z  (UTC) 
                              ####-##-##T##:##:##.000Z
                              ####-##-##T##:##:##(+/-)##:## (UTC TIme Zone Offsets)
                            
            (<year>-<month>-<day>T<hour>-<minute>(T/<+/-time offset)    
        """
        # validate date format "2000-05-19T15:51:46Z"
        #timezone_utc = pytz.timezone("UTC")
        
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
                dt = datetime.strptime(dt_s,"%Y-%m-%d %H-%M-%S").astimezone(timezone_loc)
            except:
                return 0

        elif  ( len(re.findall(reg_expr_utc2, datetime_s)) == 1 ): # utc2 format
            datetime_s = datetime_s[:-5] + "+00:00" 
        elif ( len(re.findall(reg_expr_utc, datetime_s)) == 1 ): # utc format
            datetime_s = datetime_s[:-1] + "+00:00" 
        elif ( len(re.findall(reg_expr_tz, datetime_s)) == 1 ): # time zone format  
            pass # this time zone already has the correct format
        else:
            print(f"can't evaluate, time format {datetime_s} ")
            return 0
        
        if dt is None:
            # omit colon
            try:
                dt_s = datetime_s[:-3]+datetime_s[-2:]
                dt = datetime.strptime(dt_s, "%Y-%m-%dT%H:%M:%S%z")
            except:
                return 0
        
        if debug is True:
            print(f"IN:{datetime_s_in}, dt:{dt}, tz:{dt.tzinfo} utc:{dt.utcoffset()}, dst:{dt.tzinfo.dst(dt)}")            



        ts = int(dt.timestamp())
        
        return ts

    # checks for closest value in a sorted (!) list, returns index
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