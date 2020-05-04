import json
import sqlite3
import datetime
import math
import requests
import string
import time

visits_db = '__HOME__/locations.db'

st_pop = dict()
st_pop["AK"] = 731545
st_pop["AL"] = 4903000
st_pop["AR"] = 3018000
st_pop["AZ"] = 7279000
st_pop["CA"] = 39510000
st_pop["CO"] = 5759000
st_pop["CT"] = 3565000
st_pop["DC"] = 702455
st_pop["DE"] = 973764
st_pop["FL"] = 21480000
st_pop["GA"] = 10620000
st_pop["HI"] = 1416000
st_pop["IA"] = 3155000
st_pop["ID"] = 1787000
st_pop["IL"] = 12670000
st_pop["IN"] = 6732000
st_pop["KS"] = 2913000
st_pop["KY"] = 4468000
st_pop["LA"] = 4649000
st_pop["MA"] = 6893000
st_pop["MD"] = 6046000
st_pop["ME"] = 1344000
st_pop["MI"] = 9987000
st_pop["MN"] = 5640000
st_pop["MO"] = 6137000
st_pop["MS"] = 2976000
st_pop["MT"] = 1069000
st_pop["NC"] = 1049000
st_pop["ND"] = 762062
st_pop["NE"] = 1934000
st_pop["NH"] = 1360000
st_pop["NJ"] = 8882000
st_pop["NM"] = 2097000
st_pop["NV"] = 3080000
st_pop["NY"] = 19450000
st_pop["OH"] = 11690000
st_pop["OK"] = 3957000
st_pop["OR"] = 4218000
st_pop["PA"] = 12800000
st_pop["RI"] = 1059000
st_pop["SC"] = 5149000
st_pop["SD"] = 884659
st_pop["TN"] = 6829000
st_pop["TX"] = 29000000
st_pop["UT"] = 3206000
st_pop["VA"] = 8536000
st_pop["VT"] = 623989
st_pop["WA"] = 7615000
st_pop["WI"] = 5822000
st_pop["WV"] = 1792000
st_pop["WY"] = 578759

def request_handler(request):
    def average_weight(entries,time_now,infected_list):
        if len(entries)>0:
            sum = 0
            data = dict()
            for entry in entries:
                # Get state of person
                loc = (entry[1], entry[2])
                loc_string = str(loc[0]) + "," + str(loc[1])
                r = requests.get("""https://maps.googleapis.com/maps/api/geocode/json?latlng={}&key=AIzaSyDvVizVjnvuSofxwp5IbWAoaJrp718YHus""".format(loc_string))
                response = json.loads(r.text)
                state = response['results'][0]['address_components'][5]['short_name']
                state_pop = st_pop[state]

                # Get information on # of infections in state of interest
                r2 = requests.get("""https://covidtracking.com/api/v1/states/current.json""")
                response2 = json.loads(r2.text)
                for s in response2:
                    if s['state'] == state:
                        infected_pop = s['positive']

                # Find percent of population infected
                percent_infected = infected_pop/state_pop

                if loc in data:                        
                # line['weight'] = hl_func(time_now,entry[3])
                    # data[loc] += hl_func(time_now,entry[3])

                    if entry[0] in infected_list:
                        data[loc] += hl_func(time_now,entry[3])
                    else:
                        data[loc] += hl_func(time_now,entry[3])*percent_infected
                else:
                    # data[loc] = hl_func(time_now,entry[3])

                    if entry[0] in infected_list:
                        data[loc] = hl_func(time_now,entry[3])
                    else:
                        data[loc] = hl_func(time_now,entry[3])*percent_infected
            for d in data:
                sum += data[d]
            return sum/len(entries)
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
                
                covid_Prob_List = []

                R = 6371 #radius of the earth
                lat_kil = math.degrees(1/R) #1km in latitude degree (constant)

                infected_users_raw = c.execute('''SELECT username FROM locations_table WHERE con = 1;''').fetchall()
                infected_users = []
                for i in infected_users_raw: 
                    name = i[0]
                    if name not in infected_users:
                        infected_users.append(name)

                # conn.commit() # commit commands
                # conn.close()
                # return infected_users
                i=0
                while i<len(locations_list)-1:
                    lat = locations_list[i]
                    lon = locations_list[i+1]
                    lon_kil = math.degrees(1/R/math.cos(math.radians(lat))) #1km in longitude degree (changes based on latitude)

                    entries = c.execute('''SELECT * FROM locations_table 
                                        WHERE latitude BETWEEN ?-? AND ?+?
                                        AND
                                        longitude BETWEEN ?-? AND ?+?;''', (lat,lat_kil,lat,lat_kil,lon,lon_kil,lon,lon_kil)).fetchall()
                    # return entries
                    i+=2
                    # return infected_users
                    # covid_Prob_List.append(average_weight(entries,time_now,infected_users))
                    sum = 0
                    data = dict()
                    if len(entries) > 0:
                        for entry in entries:
                            # Get state of person
                            loc = (entry[1], entry[2])
                            loc_string = str(loc[0]) + "," + str(loc[1])
                            r = requests.get("""https://maps.googleapis.com/maps/api/geocode/json?latlng={}&key=AIzaSyDvVizVjnvuSofxwp5IbWAoaJrp718YHus""".format(loc_string))
                            response = json.loads(r.text)
                            state = response['results'][0]['address_components'][5]['short_name']
                            state_pop = st_pop[state]

                            # Get information on # of infections in state of interest
                            r2 = requests.get("""https://covidtracking.com/api/v1/states/current.json""")
                            response2 = json.loads(r2.text)
                            for s in response2:
                                if s['state'] == state:
                                    infected_pop = s['positive']

                            # Find percent of population infected
                            percent_infected = infected_pop/state_pop

                            # return percent_infected

                            if loc in data:                        
                            # line['weight'] = hl_func(time_now,entry[3])
                                # data[loc] += hl_func(time_now,entry[3])

                                if entry[0] in infected_users:
                                    data[loc] += hl_func(time_now,entry[3])
                                else:
                                    data[loc] += hl_func(time_now,entry[3])*percent_infected
                            else:
                                # data[loc] = hl_func(time_now,entry[3])

                                if entry[0] in infected_users:
                                    data[loc] = hl_func(time_now,entry[3])
                                else:
                                    data[loc] = hl_func(time_now,entry[3])*percent_infected
                        # return data
                        for d in data:
                            sum += data[d]
                        covid_Prob_List.append(sum/len(entries))
                    else:
                        covid_Prob_List.append(0)
                    # conn.commit() # commit commands
                    # conn.close()
                    # return covid_Prob_List
                #return "what"
                # conn.commit()
                # conn.close()
                # return entries
                conn.commit()
                conn.close()
                return covid_Prob_List
            else:
                return "Not Authorized"  
    
    return "Invalid Request"


        