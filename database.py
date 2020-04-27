import json
import sqlite3
import datetime
visits_db = '__HOME__/locations.db'

def request_handler(request):
    def hl_func(time_now,time_entry):
        fmt = '%Y-%m-%d %H:%M:%S.%f'
        time_then = datetime.datetime.strptime(time_entry, fmt)
        td = time_now - time_then
        td_mins = int(round(td.total_seconds()/60))
        return 0.5**(td_mins/390)

    if (request['method']=='GET'):
        if 'user' in request['args'] and 'password' in request['args']:
            if 'admin'==request['values']['user'] and 'adminpassword'==request['values']['password']:
                user_data = []
                entries = []
                time_now = datetime.datetime.now()

                conn = sqlite3.connect(visits_db)  # connect to that database (will create if it doesn't already exist)
                c = conn.cursor()  # move cursor into database (allows us to execute commands)
                two_weeks_ago = time_now- datetime.timedelta(days = 14) 
                c.execute('''DELETE FROM locations_table WHERE time < ?;''', (two_weeks_ago,))
                
                if 'start' in request['args'] and 'end' in request['args']:
                    start = request['values']['start']
                    end = request['values']['end']
                    entries = c.execute('''SELECT * FROM locations_table WHERE time > ? AND time < ? ORDER BY time DESC;''',(start,end)).fetchall()
                else:
                    entries = c.execute('''SELECT * FROM locations_table ORDER BY time DESC;''').fetchall()

                if entries:
                    for entry in entries:
                        line = {}
                        line['lat'] = entry[1]
                        line['lon'] = entry[2]
                        line['weight'] = hl_func(time_now,entry[3])
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
                two_weeks_ago = time_now- datetime.timedelta(days = 14) 
                c.execute('''DELETE FROM locations_table WHERE time < ?;''', (two_weeks_ago,))

                if 'start' in request['args'] and 'end' in request['args']:
                    start = request['values']['start']
                    end = request['values']['end']
                    entries = c.execute('''SELECT * FROM locations_table WHERE username = ? AND time > ? AND time < ? ORDER BY time DESC;''',(username,start,end)).fetchall()
                else:
                    entries = c.execute('''SELECT * FROM locations_table WHERE username = ? ORDER BY time DESC;''',(username,)).fetchall()
                
                if entries:
                    for entry in entries:
                        line = {}
                        line['lat'] = entry[1]
                        line['lon'] = entry[2]
                        line['weight'] = hl_func(time_now,entry[3])
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
        lon = float(request['form']['lon'])
        lat = float(request['form']['lat'])

        #still need to work on encrypting username
        user = str(request['form']['user'])
        time = datetime.datetime.now()

        conn = sqlite3.connect(visits_db)  # connect to that database (will create if it doesn't already exist)
        c = conn.cursor()  # move cursor into database (allows us to execute commands)
        c.execute('''CREATE TABLE IF NOT EXISTS locations_table (username text,latitude float, longitude float, time timestamp);''') # run a CREATE TABLE command
        c.execute('''INSERT into locations_table VALUES (?,?,?,?);''', (user,lat,lon,time))
        two_weeks_ago = datetime.datetime.now()- datetime.timedelta(days = 14) 
        c.execute('''DELETE FROM locations_table WHERE time < ?;''', (two_weeks_ago,))

        conn.commit() # commit commands
        conn.close() # close connection to database
        return "Post successful"


        