import json
import sqlite3
import datetime
import requests
import string
import time

visits_db = '__HOME__/locations.db'
update_db = '__HOME__/update.db'
infected_db = '__HOME__/infected.db'

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
st_pop["QC"] = 8485000


def request_handler(request):
    def hl_func(time_now,time_entry):
        fmt = '%Y-%m-%d %H:%M:%S.%f'
        time_then = datetime.datetime.strptime(time_entry, fmt)
        td = time_now - time_then
        td_mins = int(round(td.total_seconds()/60))
        return 0.5**(td_mins/390)

    # Only update infected population information once a day
    def check_update(state):
        time_now = datetime.datetime.now()
        one_day_ago = time_now- datetime.timedelta(days = 1) 
        conn = sqlite3.connect(update_db)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS update_table (update_time timestamp);''') # run a CREATE TABLE command
        entries = c.execute('''SELECT * FROM update_table WHERE update_time > ? ORDER BY update_time DESC;''',(one_day_ago,)).fetchone()
        if entries == None:
            # Need to get updated stats
            infected_db = '__HOME__/infected.db'
            # infected_db = "infected.db"
            conn2 = sqlite3.connect(infected_db)
            c2 = conn2.cursor()
            c2.execute('''CREATE TABLE IF NOT EXISTS infected_table (state text, cases int);''') # run a CREATE TABLE command
            c2.execute('''DELETE FROM infected_table;''')
            r2 = requests.get("""https://covidtracking.com/api/v1/states/current.json""")
            response2 = json.loads(r2.text)
            for s in response2:
                num_infected = int(s['positive'])
                st = s['state']
                c2.execute('''INSERT into infected_table VALUES (?,?);''',(st, num_infected))
            conn2.commit()
            conn2.close()
            c.execute('''INSERT into update_table VALUES (?);''',(time_now,))
            conn.commit() # commit commands
            conn.close()
            return "again"
        else:
            infected_db = '__HOME__/infected.db'
            conn2 = sqlite3.connect(infected_db)
            c2 = conn2.cursor()
            entries = c2.execute('''SELECT * FROM infected_table WHERE state = (?);''',(state,)).fetchall()
            infected_num = entries[0][1]
            conn2.commit()
            conn2.close()
            conn.commit() # commit commands
            conn.close()
            return infected_num

    if (request['method']=='GET'):
        if 'user' in request['args'] and 'password' in request['args']:
            if 'admin'==request['values']['user'] and 'adminpassword'==request['values']['password']:
                user_data = []
                entries = []
                time_now = datetime.datetime.now()

                # visits_db = "visits.db"
                visits_db = '__HOME__/locations.db'

                conn = sqlite3.connect(visits_db)  # connect to that database (will create if it doesn't already exist)
                c = conn.cursor()  # move cursor into database (allows us to execute commands)
                two_weeks_ago = time_now- datetime.timedelta(days = 3) 
                c.execute('''DELETE FROM locations_table WHERE time < ?;''', (two_weeks_ago,))
                entries = c.execute('''SELECT * FROM locations_table ORDER BY time DESC;''').fetchall()
                num_entries = len(entries)

                if entries:
                    for entry in entries:
                        # Get state of person
                        loc = (entry[1], entry[2])
                        loc_string = str(loc[0]) + "," + str(loc[1])
                        r = requests.get("""http://www.mapquestapi.com/geocoding/v1/reverse?key=yGPUKM7cJGVAlMYN8a8suPLSZVrjEM3t&location={}""".format(loc_string), timeout = None)
                        response = json.loads(r.text)
                        state = response['results'][0]['locations'][0]['adminArea3']
                        country = response['results'][0]['locations'][0]['adminArea1']
                      
                        percent_infected = 0
                        if country == 'US':
                            if state in st_pop:
                                # Only consider locations within 50 states + DC
                                state_pop = st_pop[state]

                                # Get information on # of infections in state of interest
                                if num_entries < 25:
                                    r2 = requests.get("""https://covidtracking.com/api/v1/states/current.json""")
                                    response2 = json.loads(r2.text)
                                    infected_pop = 0
                                    for s in response2:
                                        if 'state' in s:
                                            if s['state'] == state:
                                                infected_pop = s['positive']
                                else:
                                    check = check_update(state)
                                    if check == "again":
                                        return "Had to update data. Please try again."
                                    else:
                                        infected_pop = check

                                # Find percent of population infected
                                percent_infected = infected_pop/state_pop

                                line = {}
                                line['weight'] = hl_func(time_now,entry[3])*percent_infected if int(entry[4])==0 else (hl_func(time_now,entry[3]))
                                line['lat'] = entry[1]
                                line['lon'] = entry[2]
                                line['con'] = entry[4]
                                user_data.append(line)

                    conn.commit() # commit commands
                    conn.close() # close connection to database
                    json_output = json.dumps(user_data)
                    return json_output
                else:
                    conn.commit() # commit commands
                    conn.close() # close connection to database
                    return "No data exists in database"

            else:
                time_now = datetime.datetime.now()
                username = request['values']['user']
                user_data = []
                entries = []
                conn = sqlite3.connect(visits_db)  # connect to that database (will create if it doesn't already exist)
                c = conn.cursor()  # move cursor into database (allows us to execute commands)
                two_weeks_ago = time_now- datetime.timedelta(days = 3) 
                c.execute('''DELETE FROM locations_table WHERE time < ?;''', (two_weeks_ago,))
                entries = c.execute('''SELECT * FROM locations_table WHERE username = ? ORDER BY time DESC;''',(username,)).fetchall()
                
                if entries:
                    for entry in entries:
                        # Get state of person
                        loc = (entry[1], entry[2])
                        loc_string = str(loc[0]) + "," + str(loc[1])
                        r = requests.get("""http://www.mapquestapi.com/geocoding/v1/reverse?key=yGPUKM7cJGVAlMYN8a8suPLSZVrjEM3t&location={}""".format(loc_string), timeout = None)
                        response = json.loads(r.text)
                        state = response['results'][0]['locations'][0]['adminArea3']
                        country = response['results'][0]['locations'][0]['adminArea1']

                        percent_infected = 0
                        if country == 'US':
                            if state in st_pop:
                                # Only consider locations within 50 states + DC
                                state_pop = st_pop[state]

                                # Get information on # of infections in state of interest
                                if num_entries < 25:
                                    r2 = requests.get("""https://covidtracking.com/api/v1/states/current.json""")
                                    response2 = json.loads(r2.text)
                                    infected_pop = 0
                                    for s in response2:
                                        if 'state' in s:
                                            if s['state'] == state:
                                                infected_pop = s['positive']
                                else:
                                    check = check_update(state)
                                    if check == "again":
                                        return "Had to update data. Please try again."
                                    else:
                                        infected_pop = check

                                # Find percent of population infected
                                percent_infected = infected_pop/state_pop

                                line = {}
                                line['weight'] = hl_func(time_now,entry[3])*percent_infected if int(entry[4])==0 else (hl_func(time_now,entry[3]))
                                line['lat'] = entry[1]
                                line['lon'] = entry[2]
                                line['con'] = entry[4]
                                user_data.append(line)

                    conn.commit() # commit commands
                    conn.close() # close connection to database
                    json_output = json.dumps(user_data)
                    return json_output
                else:
                    conn.commit() # commit commands
                    conn.close() # close connection to database
                    return "No data exists for user"
        
        return "Incorrect query"

    elif (request['method']=='POST'):
        con = 0
        lon = float(request['form']['lon'])
        lat = float(request['form']['lat'])

        #still need to work on encrypting username
        user = str(request['form']['user'])
        time = datetime.datetime.now()

        # visits_db = "visits.db"
        visits_db = '__HOME__/locations.db'
        conn = sqlite3.connect(visits_db)  # connect to that database (will create if it doesn't already exist)
        c = conn.cursor()  # move cursor into database (allows us to execute commands)
        c.execute('''CREATE TABLE IF NOT EXISTS locations_table (username text,latitude float, longitude float, time timestamp, con int);''') # run a CREATE TABLE command

        most_recent_con_value = (c.execute('''SELECT con FROM locations_table WHERE username = ? ORDER BY time DESC;''',(user,)).fetchone())

        if 'confirmed' not in request['form']:
            con = most_recent_con_value[0] if most_recent_con_value!=None else 0
        else:
            if most_recent_con_value!=None:
                if most_recent_con_value[0] == 0 and str(request['form']['confirmed'])=='true':
                    sql = ''' UPDATE locations_table
                            SET con = 1 
                            WHERE username = ?'''
                    c.execute(sql,(user,))
                
            if str(request['form']['confirmed'])=='true':
                con = 1
            elif str(request['form']['confirmed'])=='false':
                con = 0
        
        c.execute('''CREATE TABLE IF NOT EXISTS locations_table (username text,latitude float, longitude float, time timestamp, con int);''') # run a CREATE TABLE command

        c.execute('''INSERT into locations_table VALUES (?,?,?,?,?);''', (user,lat,lon,time,con))
        
        two_weeks_ago = datetime.datetime.now()- datetime.timedelta(days = 3) 
        c.execute('''DELETE FROM locations_table WHERE time < ?;''', (two_weeks_ago,))

        conn.commit() # commit commands
        conn.close() # close connection to database
        return "Post successful"


        