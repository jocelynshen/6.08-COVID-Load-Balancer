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

# Based on Doremalen et al., virus on worst-case surfaces (plastic and stainless steel) can last up to 72 hours, with half life occuring 6 hours

# VARIABLES (0 for OFF, 1 for ON)
insert_10_more = 0
print_entries = 0
print_weights = 0
print_heatmap = 0

def weights(insert_10_more, print_entries, print_weights, print_heatmap):
	# Get Current Time
	time_now = datetime.datetime.now()

	# Setting up example database
	COVID_db = "covid.db" # just come up with name of database
	conn = sqlite3.connect(COVID_db)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS covid_table (user text,lat int, lon int, timing timestamp);''')
	seventytwo_hours_ago = datetime.datetime.now()-datetime.timedelta(hours = 72)
	c.execute('''DELETE FROM covid_table WHERE timing < ?;''',(seventytwo_hours_ago,))
	if insert_10_more:
		for x in range(10):
			user = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(10)) #make random user name
			lat = random.randint(0,5)
			lon = random.randint(0,5)
			time_ago = random.randint(0,6000)
			time = datetime.datetime.now() - datetime.timedelta(minutes = time_ago)
			c.execute('''INSERT into covid_table VALUES (?,?,?,?);''',(user,lat,lon,time))
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
			data[lon][lat] = w
		fig, ax = plt.subplots()
		im = ax.imshow(data) 
		for i in range(6):
			for j in range(6):
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
		loc = (entry[1], entry[2])
		time_then = datetime.datetime.strptime(entry[3], fmt)
		td = time_now - time_then
		td_mins = int(round(td.total_seconds()/60))
		if td_mins < 4320:
			if loc in weights:
				weights[loc][0] += hl_func(td_mins)
				weights[loc][1] += 1
			else:
				weights[(loc)] = [hl_func(td_mins), 1]
	return weights

print(weights(1,1,1,1))

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


