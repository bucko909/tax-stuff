records = []
var_list = dict()
key_list = []
log = []
state_name = None

def state(name):
	global state_name
	state_name = name

def record():
	rec = dict()
	for (name, raw_value) in var_list:
		if isinstance(raw_value, dict):
			value = dict((key, raw_value[key]) for key in key_list)
		else:
			value = dict((key, raw_value(key)) for key in key_list)
		rec[name] = value
	global log
	records.append((state_name, rec, list(log)))
	log = []

def setup(new_key_list, new_var_list):
	global key_list
	key_list = new_key_list
	global var_list
	var_list = new_var_list

def out(text):
	log.append(text)

def render():
	print '<table>'
	print '<tr><td></td>'
	for name in key_list:
		print '''<th colspan="%i">%s</th>''' % (len(var_list), name)
	print '</tr><tr><td></td>'
	for _ in key_list:
		for (name, _) in var_list:
			print '''<th>%s</th>''' % (name,)
	print '</tr>'
	for name, rec, _ in records:
		print '<tr><th>%s</th>' % (name,)
		for key_name in key_list:
			for var_name, _ in var_list:
				print '<td>%s</td>' % (rec[var_name][key_name],)
		print '</tr>'
	print '</table>'
	for name, _, log in records:
		print '<h2>%s</h2>' % (name,)
		for line in log:
			print '<p>%s</p>' % (line,)

def summary(name):
	#out("Total profit (%s)" % (name,), -outlay[name])
	#out("Total income (%s)" % (name,), income[name])
	out("Total profit (%s)" % (name,), income[name] - outlay[name])

def summaries(after):
	print "<h2>%s</h2>" % (after,)
	summary('personal')
	if 'personal_2ndhouse' in income:
		summary('personal_2ndhouse')
	summary('llc')
	summary('savings')
