import json
import sqlite3
import datetime
import math

visits_db = '__HOME__/locations.db'

def request_handler(request):
    def average_weight(time_list,time_now):
        if len(time_list)>0:
            sum = 0
            for time in time_list:
                sum+=hl_func(time_now,time[0])
            return sum/len(time_list)
        return 0

    def hl_func(time_now,time_entry):
        fmt = '%Y-%m-%d %H:%M:%S.%f'
        time_then = datetime.datetime.strptime(time_entry, fmt)
        td = time_now - time_then
        td_mins = int(round(td.total_seconds()/60))
        return 0.5**(td_mins/390)

    if (request['method']=='GET'):
        if 'user' in request['args'] and 'password' in request['args'] and 'locations' in request['args']:
            if 'admin'==request['values']['user'] and 'adminpassword'==request['values']['password']:
                locations_list = request['values']['locations']
                locations_list = locations_list.split(",")
                locations_list = list(map(float, locations_list))

                time_now = datetime.datetime.now()
                conn = sqlite3.connect(visits_db)  # connect to that database (will create if it doesn't already exist)
                c = conn.cursor()  # move cursor into database (allows us to execute commands)
                
                #one with high probabiliy, 0 probabiliy, low probability
                covid_Prob_List = []

                R = 6371
                radius = 1 #km
                lat_kil = math.degrees(radius/R)

                i=0
                while i<len(locations_list)-1:
                    lat = locations_list[i]
                    lon = locations_list[i+1]
                    lon_kil = math.degrees(radius/R/math.cos(math.radians(lat)))

                    entries = c.execute('''SELECT time FROM locations_table 
                                        WHERE latitude BETWEEN ?-? AND ?+?
                                        AND
                                        longitude BETWEEN ?-? AND ?+?;''', (lat,lat_kil,lat,lat_kil,lon,lon_kil,lon,lon_kil)).fetchall()
                    i+=2
                    covid_Prob_List.append(average_weight(entries,time_now))

                return covid_Prob_List
            else:
                return "Not Authorized"  
    
    return "Invalid Request"


        