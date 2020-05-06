import json
import sqlite3
import datetime
import requests
import string
import time

visits_db = '__HOME__/locations.db'

def request_handler(request):
    if (request['method']=='POST'):
        if 'user' in request['form'] and 'password' in request['form'] and 'confirmed' in request['form']:
            user = str(request['form']['user'])
            confirmed_state = str(request['form']['confirmed'])

            time_now = datetime.datetime.now()
            conn = sqlite3.connect(visits_db)  # connect to that database (will create if it doesn't already exist)
            c = conn.cursor()  # move cursor into database (allows us to execute commands)
            two_weeks_ago = time_now- datetime.timedelta(days = 14) 
            c.execute('''DELETE FROM locations_table WHERE time < ?;''', (two_weeks_ago,))

            if (confirmed_state == 'true'):
                sql = ''' UPDATE locations_table
                        SET con = 1 
                        WHERE username = ?'''
                c.execute(sql,(user,))
            elif (confirmed_state == 'false'):
                sql = ''' UPDATE locations_table
                        SET con = 0 
                        WHERE username = ?'''
                c.execute(sql,(user,))

            conn.commit() # commit commands
            conn.close() # close connection to database
            return "COVID state changed for "+user
            
    return "Invalid Request"