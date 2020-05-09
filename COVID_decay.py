import numpy as np
import scipy as sp
import scipy.optimize
import matplotlib
import matplotlib.pyplot as plt
import sqlite3
import random
import string
import datetime
import time
import requests
import json

#Dictionary of state population information (50 states + DC)
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

# Based on Doremalen et al., virus on worst-case surfaces (plastic and stainless steel) can last up to 72 hours, with half life occuring 6 hours

# VARIABLES (0 for OFF, 1 for ON)
insert = 1
print_entries = 1
print_weights = 1
print_heatmap = 1

def weights(insert, print_entries, print_weights, print_heatmap):
	# Get Current Time
	time_now = datetime.datetime.now()

	# Setting up example database
	COVID_db = "covid.db" # just come up with name of database
	conn = sqlite3.connect(COVID_db)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS covid_table (user text,lat int, lon int, timing timestamp, confirmed int);''')
	seventytwo_hours_ago = datetime.datetime.now()-datetime.timedelta(hours = 72)
	c.execute('''DELETE FROM covid_table WHERE timing < ?;''',(seventytwo_hours_ago,))
	trial = c.execute('''SELECT user FROM covid_table WHERE confirmed = 1;''').fetchall()
	conn.commit()
	conn.close()
	return trial
	if insert:
		users = ["Abraham", "Jocelyn", "Jackie", "Amanda", "Annie", "Joe"]
		infected_list = []
		x_locs = [40.714224]
		for i in range(1,6):
			x_locs.append(round(x_locs[0]+0.000001*i,6))
		y_locs = [-73.961452]
		for j in range(1,6):
			y_locs.append(round(y_locs[0]+0.000001*j,6))
		# insert 20 random
		for x in range(20):
			# user = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(10)) #make random user name
			u = str(random.choice(users))
			# lat = random.randint(0,5)
			lat = random.choice(x_locs)
			# lon = random.randint(0,5)
			lon = random.choice(y_locs)
			time_ago = random.randint(0,4320)
			time = datetime.datetime.now() - datetime.timedelta(minutes = time_ago)
			if u not in infected_list:
				infect_chance = [0,0,0,0,1]
				infected = random.choice(infect_chance)
			else:
				infected = 1
			if ((u not in infected_list) and (infected == 1)):
				# if u == "Abraham":
				# 	c.execute('''UPDATE covid_table SET confirmed = 1 WHERE user = 'Abraham';''')
				# elif u == "Jocelyn":
				# 	c.execute('''UPDATE covid_table SET confirmed = 1 WHERE user = 'Jocelyn';''')
				# elif u == "Jackie":
				# 	c.execute('''UPDATE covid_table SET confirmed = 1 WHERE user = 'Jackie';''')
				# elif u == "Amanda":
				# 	c.execute('''UPDATE covid_table SET confirmed = 1 WHERE user = 'Amanda';''')
				# elif u == "Annie":
				# 	c.execute('''UPDATE covid_table SET confirmed = 1 WHERE user = 'Annie';''')
				# elif u == "Joe":
				# 	c.execute('''UPDATE covid_table SET confirmed = 1 WHERE user = 'Joe';''')
				c.execute('''UPDATE covid_table SET confirmed = 1 WHERE user = ''' + u + ''';''')
				infected_list.append(u)
			c.execute('''INSERT into covid_table VALUES (?,?,?,?,?);''',(u,lat,lon,time,infected))
	things = c.execute('''SELECT * FROM covid_table ORDER BY timing DESC;''').fetchall()
	conn.commit()
	conn.close()
	weights = find_weights(things, time_now)
	if print_entries:
		for x in things:
			print(x)
	if print_weights:
		print(weights)
	if print_heatmap:
		data = np.array([[0.0,0.0,0.0,0.0,0.0,0.0],
				 [0.0,0.0,0.0,0.0,0.0,0.0],
				 [0.0,0.0,0.0,0.0,0.0,0.0],
				 [0.0,0.0,0.0,0.0,0.0,0.0],
				 [0.0,0.0,0.0,0.0,0.0,0.0],
				 [0.0,0.0,0.0,0.0,0.0,0.0]])
		for key in weights:
			lat = key[0]
			lon = key[1]
			w = weights[key][0]
			data[int(round((lon+73.961452)*1000000))][int(round((lat-40.714224)*1000000))] = w
		fig, ax = plt.subplots()
		im = ax.imshow(data)
		ax.set_xticks(np.arange(6))
		ax.set_yticks(np.arange(6))
		ax.set_xticklabels([24,25,26,27,28,29])
		ax.set_yticklabels([52,51,50,49,48,47])
		x_locs = [40.714224]
		y_locs = [-73.961452]
		for i in range(1,6):
			x_locs.append(round(x_locs[0]+0.000001*i,6))
		for j in range(1,6):
			y_locs.append(round(y_locs[0]+0.000001*j,6))
		for xl in x_locs:
			for yl in y_locs:
				j = int(round((yl+73.961452)*1000000))
				# print((yl+73.961452)*1000000)
				# print(j)
				i = int(round((xl-40.714224)*1000000))
				# print((xl-40.714224)*1000000)
				# print(i)
				text = ax.text(j, i, round(data[i, j],2),
                       ha="center", va="center", color="w")
		fig.tight_layout()
		plt.show()

#Determines percentage of virus still left after t minutes
# 6.5 hours = 390 minutes
def hl_func(t):
	return 0.5**(t/390)

#Returns weight for each location
def find_weights(things, time_now):
	fmt = '%Y-%m-%d %H:%M:%S.%f'
	weights = dict()
	for entry in things:
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

		# Update weight
		time_then = datetime.datetime.strptime(entry[3], fmt)
		td = time_now - time_then
		td_mins = int(round(td.total_seconds()/60))
		if td_mins < 4320:
			if loc in weights:
				if entry[4] == 0:
					weights[loc][0] += hl_func(td_mins)*percent_infected
					weights[loc][1] += 1
				else:
					weights[loc][0] += hl_func(td_mins)
					weights[loc][1] += 1
			else:
				if entry[4] == 0:
					weights[loc] = [hl_func(td_mins)*percent_infected, 1]
				else:
					weights[loc] = [hl_func(td_mins), 1]
	return weights

# print(int(round(4.999)))
print(weights(insert,print_entries,print_weights,print_heatmap))

# def fit_exp_linear(t, y, C=0):
#     y = y - C
#     y = np.log(y)
#     K, A_log = np.polyfit(t, y, 1)
#     A = np.exp(A_log)
#     return A, K

# def model_func(t, A, K, C):
#     return A * np.exp(K * t) + C

# def fit_exp_nonlinear(t, y):
#     opt_parms, parm_cov = sp.optimize.curve_fit(model_func, t, y, maxfev=1000)
#     A, K, C = opt_parms
#     return A, K, C

# t = np.asarray([0.0000001,6,72])
# y = np.asarray([1,0.5,0.000000000000000001])
# #
# A, K = fit_exp_linear(t,y)
# # A, K, C = fit_exp_nonlinear(t,y)
# print(A,K)

# A0, K0, C0 = 2.5, -4.0, 2.0
# tmin, tmax = 0,0.5
# num = 20
# t = np.linspace(tmin, tmax, num)

# def model_func(t, A, K, C):
#     return A * np.exp(K * t) + C

# y = model_func(t, A0, K0, C0)
# A, K = fit_exp_linear(t, y, C0)
# print(A, K)


