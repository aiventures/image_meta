import re
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.parser import parse
from dateutil.tz import tzutc
from dateutil.tz import tzoffset
from math import ceil
from math import log
from math import floor
from functools import reduce
import pytz

class Util:
    """ util module """

    NOT_FOUND = -1

    @staticmethod
    def get_datetime_from_string(datetime_s:str,local_tz='Europe/Berlin',debug=False):
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

        if dt_in is None:
            return None
        
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
            out = int(dt_utc.timestamp())
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

        if ((value is None) or
           (isinstance(sorted_list,list) and len(sorted_list) == 0)):
            return Util.NOT_FOUND
        
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
    def print_dict_info(d:dict,s="",show_info=True,list_elems=9999,num_spaces=4):
        """ prints information in dictionary """
        
        sp = " " * num_spaces

        if not show_info:
            return

        if s != "":
            print(f"--- Dictionary Content {s} ---")

        for k,v in d.items():
            s = ""
            n = 0
            if ( isinstance(v,list) or isinstance(v,tuple) ):
                n = min(len(v),list_elems)
                print(f"{sp}Element {k} has list with {len(v)} elements, showing {n} elements")                
                print(f"{sp}{k}  ->  {v[:n]}")
            elif isinstance(v,dict):
                n = min(len(v.keys()),list_elems)
                print(f"{sp}Element {k} has dictionary with {len(v.keys())} attributes, showing {n} attributes")
                d_keys = list(v.keys())[:n]
                s = f"{sp}{k}  ->  "
                for d_key in d_keys:
                    s += f"\n{sp}{d_key}:{v[d_key]}"
                print(s)
            else:
                print(f"{sp}{k}  ->   {v}")

    @staticmethod
    def get_easter_sunday(year:int,verbose=False,showinfo=False):
        """ Calculates easter sunday
            Arguments
            year: Year 
            verbose: if true returns a detailed dictionary of calculations date object otherwise
            showinfo: show information
            Returns: Date or Info Dictionary of Easter Sunday
            Reference: https://www.tondering.dk/claus/cal/easter.php 
        """
        G = ( year % 19 ) + 1
        epact_julian = (11*(G-1)) % 30 # epact in julian calendar
        C = ( year // 100 ) + 1 # century
        S = (3*C) // 4 # solar equation, difference Julian vs. Gregorian
        L = (8*C+5) // 25 # Lunar Equation, difference between the Julian calendar and the Metonic cycle.  

        # Gregorian EPact
        # The number 8 is a constant that calibrates the starting point of the Gregorian Epact so 
        # that it matches the actual age of the moon on new year’s day.
        epact_gregorian = ( epact_julian - S + L + 8 )
        
        # adjust so that gregorian epact is within range of 1 to 30
        if epact_gregorian == 0:
            epact_gregorian = 30
        elif ( epact_gregorian > 30 ) or ( epact_gregorian < 0):
            epact_gregorian = epact_gregorian % 30
                
        # now calculate paschal full moon
        if epact_gregorian < 24:
            d_fm = date(year, 4, 12)
            d_offset = epact_gregorian - 1 
        else:    
            d_fm = date(year, 4, 18)
            d_offset = epact_gregorian % 24
            if epact_gregorian > 25:
                d_offset -= 1
            # April 18 otherwise April 17
            elif ( epact_gregorian == 25 ) and ( G < 11 ):
                d_offset -= 1
                
        d_fm = d_fm - timedelta(days=d_offset)
        d_weekday = d_fm.isoweekday()
        
        # offset calculate nex sunday / in case its a sunday it will be follow up sunday
        d_e_offset = 7 - ( d_weekday % 7 )
        d_easter = d_fm + timedelta(days=d_e_offset)
        if showinfo:   
            print(f" {year}|G:{str(G).zfill(2)} Epact:{str(epact_gregorian).zfill(2)}|C:{C} S:{S} L:{L}"+
                f"|F.Moon {d_fm}-{d_fm.strftime('%a')}|Eastern {d_easter}/{d_easter.strftime('%a')}|")
        
        # Return Easter Sunday either as date only or as detailed dictionary
        if verbose:
            d_easter_dict = {}
            d_easter_dict["golden_number"] = G
            d_easter_dict["epact_julian"] = epact_julian
            d_easter_dict["century"] = C
            d_easter_dict["solar_equation"] = S
            d_easter_dict["lunar_equation"] = L
            d_easter_dict["epact_gregorian"] = epact_gregorian
            d_easter_dict["date_full_moon"] = d_fm
            d_easter_dict["isoweekday_full_moon"] = d_weekday
            d_easter_dict["date_eastern"] = d_easter        
            return d_easter_dict
        else:
            return d_easter                

    @staticmethod
    def get_holiday_dates(year:int,show_info=False):
        """ Calculates holiday dates for Badenwürttemberg for given year """

        holiday_list = {"Neujahr":{"month":1,"day":1,"holiday":1},
                        "Dreikönig":{"month":1,"day":6,"holiday":1},
                        "Rosenmontag":{"holiday":0,"offset":-48},
                        "Aschermittwoch":{"holiday":0,"offset":-46},
                        "Karfreitag":{"holiday":1,"offset":-2},
                        "Ostersonntag":{"holiday":0,"offset":0},
                        "Ostermontag":{"holiday":1,"offset":1},
                        "1.Mai":{"month":5,"day":1,"holiday":1},
                        "Himmelfahrt":{"holiday":1,"offset":39},
                        "Pfingstsonntag":{"holiday":0,"offset":49},
                        "Pfingstmontag":{"holiday":1,"offset":50},
                        "Fronleichnam":{"holiday":1,"offset":60},        
                        "Dt Einheit":{"month":10,"day":3,"holiday":1},
                        "Allerheiligen":{"month":11,"day":1,"holiday":1},
                        "Heiligabend":{"month":12,"day":24,"holiday":1},
                        "1.Weihnachtstag":{"month":12,"day":25,"holiday":1},
                        "2.Weihnachtstag":{"month":12,"day":26,"holiday":1},
                        "Silvester":{"month":12,"day":31,"holiday":1}}
                        
        d_easter = Util.get_easter_sunday(year)

        out_dict ={}
        num_holidays = 0

        if show_info:
            print(f"\n--- Holiday Days for year {year} ---")

        for h,v in holiday_list.items():
            # check if it is a fixed holiday
            offset = holiday_list[h].get("offset",None)        
            if offset is None:
                d_holiday = date(year,v["month"],v["day"])
            else:
                d_holiday = d_easter + timedelta(days=v["offset"])
            
            weekday = d_holiday.isoweekday()    
            v["weekday"] = weekday
            v["year"] = year
            v["d"] = d_holiday
            v["name"] = h    
            if weekday >= 6:
                v["holiday"] = 0
            out_dict[d_holiday] = v
            
            if show_info:
                num_holidays += v["holiday"]
                print(f"{d_holiday.strftime('%Y-%B-%d (%A)')}: {h} ({v['holiday']})")
        if show_info:
            print(f"--- Number of Holiday Days {year}: {num_holidays} ---")
        
        return out_dict

    @staticmethod
    def is_leap_year(y):
        """ check whether year is leap year """
        ly = False
        
        if ( y % 4 == 0 ) and not ( y % 100 == 0 ):
            ly = True

        if ( y % 100 == 0 ) and not ( y % 400 == 0 ):
            ly = False

        if ( y % 400 == 0 ):
            ly = True

        return ly        

    @staticmethod
    def get_1st_isoweek_date(y:int):
        """ returns monday date of first isoweek of a given calendar year 
            https://en.wikipedia.org/wiki/ISO_week_date
            W01 is the week containing 1st Thursday of the Year    
        """
        d_jan1 = date(y,1,1)
        wd_jan1 = d_jan1.isoweekday()
        # get the monday of this week
        d_monday_w01 = d_jan1 - timedelta(days=(wd_jan1-1))
        # majority of days in new calendar week
        if wd_jan1 > 4:
            d_monday_w01 += timedelta(days=7)
            
        return d_monday_w01

    @staticmethod
    def get_isoweekyear(y:int):
        """" returns isoweek properties for given calendar year as dictionary:
            1st and last monday of isoweek year, number of working weeks
        """
        d_first = Util.get_1st_isoweek_date(y)
        d_last = Util.get_1st_isoweek_date(y+1) 
        working_weeks = (d_last - d_first).days // 7
        d_last = Util.get_1st_isoweek_date(y+1) - timedelta(days=7)
        isoweekyear = {}
        isoweekyear["first_monday"] = d_first
        isoweekyear["last_monday"] = d_last
        isoweekyear["last_day"] = d_last + timedelta(days=6)
        isoweekyear["weeks"] = working_weeks
        isoweekyear["year"] = y

        return isoweekyear        

    @staticmethod
    def isoweek(d:date):
        """" returns isoweek (isoweek,calendar year,number of passed days in calendar year) for given date """
        y = d.year
        
        wy = Util.get_isoweekyear(y)
        
        # check if date is in boundary of current calendar year    
        if ( d < wy["first_monday"] ):
            wy = Util.get_isoweekyear(y-1)
        elif ( d > wy["last_day"] ):
            wy = Util.get_isoweekyear(y+1)
            
        iso = {}
        iso["year"] = wy["year"]
        iso["leap_year"] = Util.is_leap_year(wy["year"])
        iso["weeks_year"] = wy["weeks"]    
        iso["day_in_year"] = ( d - wy["first_monday"]).days + 1
        iso["calendar_week"] = ceil( iso["day_in_year"] / 7 ) 
        iso["weekday"] = d.isoweekday()
        
        return iso

    @staticmethod
    def byte_info(x:int,short:bool=True,num_decimals:int=1):
        """ returns formatted size in bytes 
            Parameters
            ----------
            x : int
                Byte size (integer)
            short: boolean, optional (default True)
                output as string or dictionary
            num_decimals: int, optional (default 1)
                number of decimals
            Returns
            -------
            str,dict
                depending on short flag, formatted string or dictionary with all conversion details
        """
        
        ld_x = log(x,2**10) # exponent to base 1024
        exp_int = floor(ld_x)
        exp_frac = ld_x - exp_int
        units = ("","Kilo","Mega","Giga","Tera","Peta","Exa","Zetta","Yotta")
        value = (2**10)**exp_frac
        text = str(round(value,num_decimals))+" "+units[exp_int]+"bytes"
        if short:
            r = text
        else:
            r = {}
            r["value_int"] = x
            r["power_int_1024"] = exp_int
            r["power_frac_1024"] = exp_frac
            r["value"] = round(value,num_decimals)
            r["units"] = units[exp_int]
            r["text"] = text
        
        return r

    @staticmethod
    def contains(s:str,substrings=None):
        """ checks if substring contained in a list is contained in a given string (case insensitive) """
        if substrings is None:
            return None
        if isinstance(substrings,str):
            substrings = [substrings]
        if not (isinstance(substrings,list)):
            return False
        l = list(map(lambda i:i.lower() in s.lower(),substrings))
        if len(l) == 0:
            return False

        return reduce(lambda a,b:a or b,l)        

    
