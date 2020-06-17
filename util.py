import re
from datetime import datetime
import pytz

class Util:
    """ util module """

    @staticmethod
    def get_timestamp(datetime_s:str,) -> int:
        """ returns UTC timestamp for date string 
            allowed formats:  ####-##-##T##:##:##Z  (UTC) 
                              ####-##-##T##:##:##.000Z
                              ####-##-##T##:##:##(+/-)##:## (UTC TIme Zone Offsets)
                            
            (<year>-<month>-<day>T<hour>-<minute>(T/<+/-time offset)    
        """
        # validate date format "2000-05-19T15:51:46Z"
        timezone_utc = pytz.timezone("UTC")
        reg_expr_utc = "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"
        reg_expr_utc2 = "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}[.]000Z$"
        reg_expr_tz = "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}[+-]\\d{2}:\\d{2}$"
        is_utc_format = ( len(re.findall(reg_expr_utc, datetime_s)) == 1 )
        is_utc_format2 = ( len(re.findall(reg_expr_utc2, datetime_s)) == 1 )
        is_tz_format = ( len(re.findall(reg_expr_tz, datetime_s)) == 1 )
        if not ( is_utc_format or is_utc_format2 or is_tz_format):
            print(f"can't evaluate, time format is expected of type ####-##-##T##:##:##(Z|+/-##:##), not {datetime_s} ")
            return 0
        
        # change timestamp format
        if is_utc_format:
            datetime_s = datetime_s[:-1] + "+00:00" 
        
        if is_utc_format2:
            datetime_s = datetime_s[:-5] + "+00:00" 

        # omit colon
        dt_s = datetime_s[:-3]+datetime_s[-2:]
        dt = datetime.strptime(dt_s, "%Y-%m-%dT%H:%M:%S%z")
        # convert to utc
        dt = ( dt - dt.utcoffset() ).replace(tzinfo=None) 
        dt = timezone_utc.localize(dt)
        return int(dt.timestamp())

    # checks for closest value in a sorted (!) list, returns index
    @staticmethod
    def get_nearby_index(value,sorted_list:list):
        """ returns index for closest value in a sorted list for a given input value,
            uses binary search
        """
        
        idx = -1
        idx_min = 0
        idx_max = len(sorted_list)
        idx_old = -2
        
        finished = False    
        
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
        
        return idx