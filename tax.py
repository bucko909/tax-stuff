#personal_allowance = 8105
#corporation_tax_rate = [(0, 0), (10000, 0.19)]
#income_tax = [(0, 0.2), (34370, 0.4), (150000, 0.45)]
#savings_tax = [(0, 0.1), (2710, 0.2)] + income_tax[1:]
#dividend_rate_raw = [(0, 0.1), (34370, 0.325), (150000, 0.425)]
#dividend_rate = []
#for (low, rate) in dividend_rate_raw:
#	dividend_rate.append((low, rate * 10.0/9.0 - 1/9.0))
#stamp_duty_rate = [(0, 0), (125000, 0.01), (250000, 0.03), (500000, 0.04), (1000000, 0.05), (2000000, 0.07)] # Ignoring the 15% nonsense.
#capital_gains_tax = [(0, 0), (10600, 0.18), (34370, 0.28)]
personal_allowance = 9440
corporation_tax_rate = [(0, 0), (10000, 0.19)]
income_tax = [(0, 0.2), (32010, 0.4), (150000, 0.45)]
savings_tax = income_tax
dividend_rate_raw = [(0, 0.1), (32010, 0.325), (150000, 0.375)]
dividend_rate = []
for (low, rate) in dividend_rate_raw:
	dividend_rate.append((low, rate * 10.0/9.0 - 1/9.0))
stamp_duty_rate = [(0, 0), (125000, 0.01), (250000, 0.03), (500000, 0.04), (1000000, 0.05), (2000000, 0.07)] # Ignoring the 15% nonsense.
capital_gains_tax = [(0, 0), (10600, 0.18), (34370, 0.28)]

def inflate(rate):
	global personal_allowance
	personal_allowance *= rate
	inflate_(income_tax, rate)
	inflate_(savings_tax, rate)
	inflate_(dividend_rate_raw, rate)
	inflate_(capital_gains_tax, rate)

def inflate_(tax_profile, rate):
	for i in range(len(tax_profile)):
		tax_profile[i] = (tax_profile[i][0] * rate, tax_profile[i][1])

def rate_full(rates, amount):
	for (low, rate) in rates:
		if low > amount:
			break
		ret = rate * amount
	return ret

def rate_sensible(rates, amount):
	so_far = 0
	last_rate = 0
	total = 0
	for (low, rate) in rates:
		if low > amount:
			break
		total += (rate - last_rate) * (amount - low)
		last_rate = rate
	return total

def total_tax(income, savings, dividends, gains):
	this_personal_allowance = personal_allowance - max(0, min((income + savings + dividends - 100000)/2, personal_allowance))
	taxable_income = income - this_personal_allowance
	it = rate_sensible(income_tax, taxable_income)
	st = rate_sensible(savings_tax, taxable_income+savings) - rate_sensible(savings_tax, taxable_income)
	dt = rate_sensible(dividend_rate, taxable_income+savings+dividends) - rate_sensible(dividend_rate, taxable_income+savings)
	cg = rate_sensible(capital_gains_tax, taxable_income+savings+dividends+gains) - rate_sensible(capital_gains_tax, taxable_income+savings+dividends)
	return it+st+dt+cg

stamp_duty = lambda amount : rate_full(stamp_duty_rate, amount)
corporation_tax = lambda amount : rate_sensible(corporation_tax_rate, amount)
