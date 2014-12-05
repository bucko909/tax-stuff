#!/usr/bin/python
# -*- coding: utf8
from math import *
import collections
import tax
import simulator

import cgi

form = cgi.FieldStorage()

house_price = float(form.getfirst("house_price", 100000.0))
deposit_amount = float(form.getfirst("deposit_amount", house_price*0.25))
rent_annual = float(form.getfirst("rent_annual", house_price*0.04))
rent_annual_taxfree = float(form.getfirst("rent_annual_taxfree", house_price*0.04))
rent_loss_pc = float(form.getfirst("rent_loss_pc", 15))
rent_inflation_pc = float(form.getfirst("rent_inflation_pc", 5.0))
income_inflation_pc = float(form.getfirst("income_inflation_pc", 5.0))
expected_growth_pc = float(form.getfirst("expected_growth_pc", 5.0))
mortgage_interest_pc = float(form.getfirst("mortgage_interest_pc", 2.5))
mortgage_years = int(form.getfirst("mortgage_years", 20))
savings_interest_raw_pc = float(form.getfirst("savings_interest_raw_pc", 2.5))
tax_boundary_growth_pc = float(form.getfirst("tax_boundary_growth_pc", 3.0))
personal_income = float(form.getfirst("personal_income", 40000.0))
years = int(form.getfirst("years", 30))

mortgage_size = house_price - deposit_amount
mortgage_month_mul = (1.0 + mortgage_interest_pc / 100.0) ** (1/12.0)
if mortgage_years == 0:
	mortgage_payment_per_month = (mortgage_month_mul - 1.0) * mortgage_size
else:
	mortgage_payment_per_month = mortgage_month_mul ** (mortgage_years*12) * (mortgage_month_mul - 1.0) / (mortgage_month_mul ** (mortgage_years*12) - 1.0) * mortgage_size

# income, savings, dividends, then capital gains

print "Content-type: text/html; charset=utf-8"
print
print '''<html><head><title>Buy-to-let 2013/2014</title></head><body><h1>Buy-to-let 2013/2014</h1><p>This tool's purpose is to work out what it's worth to buy a house, in terms of rental income. It'll also give some hints about how buy-to-rent should be approached (should you set up an LLC?). It presently ignores income types for your current income; all income is assumed to be salary. This will make the output slightly wrong where you have a lot of dividend income, since savings income will increase your dividend tax. The tax boundary inflation doesn't affect stamp duty (though that doesn't really matter) and corporation tax, because the government appear to ignore those.</p><h2>Tweak values</h2><form>
<input type="text" name="house_price" value="%0.0f" /> &lt;-- price of the house, at purchase (GBP)<br />
<input type="text" name="deposit_amount" value="%0.0f" /> &lt;-- deposit (amount of the house value that isn't in the mortgage) (GBP)<br />
<input type="text" name="rent_annual" value="%0.0f" /> &lt;-- expected annual rent (raw GBP)<br />
<input type="text" name="rent_annual_taxfree" value="%0.0f" /> &lt;-- expected annual <em>tax-free</em> rent (raw GBP). Example: Rent saved by owning; Rent a Room.<br />
<input type="text" name="rent_loss_pc" value="%0.0f" /> &lt;-- expected annual rent lost to agent fees, repairs and so-on (%%)<br />
<input type="text" name="rent_inflation_pc" value="%0.2f" /> &lt;-- inflation in rent income, per year (%%)<br />
<input type="text" name="expected_growth_pc" value="%0.2f" /> &lt;-- expected inflation in house price, per year (%%)<br />
<input type="text" name="savings_interest_raw_pc" value="%0.2f" /> &lt;-- savings interest (pre-tax %%)<br />
<input type="text" name="tax_boundary_growth_pc" value="%0.2f" /> &lt;-- expected growth in tax boundaries, per year (%%)<br />
<input type="text" name="mortgage_interest_pc" value="%0.2f" /> &lt;-- mortgage interest rate (%%)<br />
<input type="text" name="mortgage_years" value="%0.0f" /> &lt;-- mortgage years<br />
<input type="text" name="personal_income" value="%0.0f" /> &lt;-- personal income (GBP)<br />
<input type="text" name="income_inflation_pc" value="%0.2f" /> &lt;-- inflation in income, per year (%%)<br />
<input type="text" name="years" value="%0.0f" /> &lt;-- years before expected sale of property<br />
<input type="submit"/>
</form>

<h2>Simulation</h2>''' % (house_price, deposit_amount, rent_annual, rent_annual_taxfree, rent_loss_pc, rent_inflation_pc, expected_growth_pc, savings_interest_raw_pc, tax_boundary_growth_pc, mortgage_interest_pc, mortgage_years, personal_income, income_inflation_pc, years)

stamp_duty = tax.stamp_duty(house_price)
mortgage_arrangement = 1500
initial_outlay = stamp_duty + deposit_amount + mortgage_arrangement

# We run three simulations: A company, a personal business and just saving the money.
income = collections.defaultdict(lambda : 0)
outlay = collections.defaultdict(lambda : initial_outlay)

def out(s, v):
	if v >= 0:
		simulator.out("<p><b>%s</b>: %0.0f</p>" % (s, v))
	else:
		simulator.out("<p><b>%s</b>: <span style=\"color: red\">%0.0f</span></p>" % (s, v))

simulator.setup(('savings', 'personal', 'llc'), [("Income", lambda key : int(income[key])), ("Outlay", lambda key : int(outlay[key])), ("Profit", lambda key : int(income[key] - outlay[key]))])
simulator.state("Initial purchase")
out("Initial outlay", initial_outlay)
out("Stamp duty", stamp_duty)
income['savings'] = initial_outlay
outlay['llc'] += 100.0 # Company registration
simulator.record()

def do_apr(model):
	ls = [0]
	for i in range(1, years+1):
		if model == 'savings':
			ls.append(simulator.records[i][1]['Outlay'][model] - sum(ls))
		else:
			ls.append(simulator.records[i][1]['Outlay'][model] - simulator.records[i][1]['Income'][model] - sum(ls))

	profit_fn = lambda rate : sum(ls[i] * (rate ** (years+1-i) - 1) for i in range(1, years+1))

	last = 1.00
	rate = 2.00
	target = simulator.records[-1][1]['Profit'][model]
	if target < 0: # or any(i < 0 for i in ls):
		return None
	while True:
		profit = profit_fn(rate)
		if abs(profit - target) < 0.00005:
			break
		old = rate
		if profit < target and rate > last:
			rate += 1.0
		else:
			if profit > target:
				rate -= abs(rate - last) / 2
			else:
				rate += abs(rate - last) / 2
		last = old
	return rate

for year in range(1, years+1):
	simulator.state('Year %i' % (year,))
	rent_income = rent_annual * (100-rent_loss_pc) / 100.0
	rent_income_taxfree = rent_annual_taxfree * (100-rent_loss_pc) / 100.0
	out("Rent after losses", rent_income)
	out("Tax-free rent after losses", rent_income_taxfree)

	# Simulate a year of mortgage payments
	mortgage_interest = 0.0
	this_outlay = 0.0
	for m in range(12):
		if mortgage_size > 0:
			mortgage_interest += mortgage_size * (mortgage_month_mul - 1.0)
			mortgage_size *= mortgage_month_mul
			mortgage_size -= mortgage_payment_per_month
			this_outlay += mortgage_payment_per_month
	outlay['llc'] += this_outlay
	outlay['personal'] += this_outlay

	# Looks like offsetting interest in a house you live in and claim as a main residence is hard. Probably 'personal' isn't allowed to receive rental income, or at least not allowed to claim tax relief on it.

	out("Mortgage interest", mortgage_interest)
	profit = rent_income - mortgage_interest
	taxable_profit = max(profit, 0) # Ignore, for now, offsetting losses
	out("Taxable profit", taxable_profit)
	income_tax = tax.total_tax(personal_income+taxable_profit, 0, 0, 0) - tax.total_tax(personal_income, 0, 0, 0)
	income['personal'] += rent_income - income_tax + rent_income_taxfree
	if income_tax:
		out("Profit tax as income", income_tax)
	outlay['savings'] += this_outlay - rent_income + income_tax
	income['savings'] += this_outlay - rent_income + income_tax

	tax_corp = tax.corporation_tax(max(profit + rent_income_taxfree - 100, 0))
	if tax_corp:
		out("Corporation tax", tax_corp)
	tax_div = tax.total_tax(personal_income, 0, taxable_profit - tax_corp, 0) - tax.total_tax(personal_income, 0, 0, 0)
	if tax_div:
		out("Profit tax as dividends", tax_div)
	income['llc'] += rent_income + rent_income_taxfree - tax_corp - tax_div
	outlay['llc'] += 100 # Accountancy

	savings_interest = savings_interest_raw_pc / 100.0 * income['savings']
	tax_sav = tax.total_tax(personal_income, savings_interest, 0, 0) - tax.total_tax(personal_income, 0, 0, 0)
	out("Savings tax", tax_sav)
	income['savings'] += savings_interest - tax_sav

	out("Mortgage size", mortgage_size)

	# Inflate things
	rent_annual *= 1.0 + rent_inflation_pc / 100.0
	rent_annual_taxfree *= 1.0 + rent_inflation_pc / 100.0
	personal_income *= 1.0 + income_inflation_pc / 100.0
	tax.inflate(tax_boundary_growth_pc / 100.0 + 1)
	simulator.record()

simulator.state('Post sale')
sale_price = house_price*(1.0+expected_growth_pc/100.0)**years
capital_gains = sale_price - house_price
out("Capital gains", capital_gains)
income['llc'] += sale_price - mortgage_size
income['personal'] += sale_price - mortgage_size

capital_gains_tax_llc = tax.total_tax(personal_income, 0, taxable_profit - tax_corp, capital_gains) - tax.total_tax(personal_income, 0, taxable_profit - tax_corp, 0)
out("Capital gains tax at sale (for LLC)", capital_gains_tax_llc)
income['llc'] -= capital_gains_tax_llc

capital_gains_tax_personal = tax.total_tax(personal_income + taxable_profit, 0, 0, capital_gains) - tax.total_tax(personal_income + taxable_profit, 0, 0, 0)
out("Capital gains tax at sale (for 2nd house)", capital_gains_tax_personal)
income['personal'] -= capital_gains_tax_personal
simulator.record()

print "<h2>Summary</h2>"

for model in ('savings', 'personal', 'llc'):
	try:
		print "<p><b>%s</b>: Naive %0.2f%%</p>" % (model, ((1+(income[model]-outlay[model])/outlay['savings'])**(1.0/years)-1)*100,)
	except:
		pass
	try:
		print "<p><b>%s</b>: Less naive %0.2f%%</p>" % (model, (do_apr(model)-1)*100)
	except:
		pass

simulator.render()

do_apr('personal')

print "</body></html>"
