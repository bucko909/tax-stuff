#!/usr/bin/python
# -*- coding: utf8
from math import *
import collections
import tax
import simulator

import cgi

form = cgi.FieldStorage()

house_price = float(form.getfirst("house_price", 125000.0))
deposit_amount = float(form.getfirst("deposit_amount", house_price*0.25))
share_people = int(form.getfirst("share_people", 4))
rent_annual_pp = float(form.getfirst("rent_annual_pp", house_price*0.04/share_people))
rent_loss_pc = float(form.getfirst("rent_loss_pc", 5))
rent_inflation_pc = float(form.getfirst("rent_inflation_pc", 5.0))
income_inflation_pc = float(form.getfirst("income_inflation_pc", 5.0))
expected_growth_pc = float(form.getfirst("expected_growth_pc", 5.0))
mortgage_interest_pc = float(form.getfirst("mortgage_interest_pc", 3.0))
mortgage_years = int(form.getfirst("mortgage_years", 20))
savings_interest_raw_pc = float(form.getfirst("savings_interest_raw_pc", 3.0))
tax_boundary_growth_pc = float(form.getfirst("tax_boundary_growth_pc", 3.0))
personal_income = float(form.getfirst("personal_income", 40000.0))
years = int(form.getfirst("years", 2))

mortgage_size = house_price - deposit_amount
mortgage_month_mul = (1.0 + mortgage_interest_pc / 100.0) ** (1/12.0)
if mortgage_years == 0:
	mortgage_payment_per_month = (mortgage_month_mul - 1.0) * mortgage_size
else:
	mortgage_payment_per_month = mortgage_month_mul ** (mortgage_years*12) * (mortgage_month_mul - 1.0) / (mortgage_month_mul ** (mortgage_years*12) - 1.0) * mortgage_size

print "Content-type: text/html; charset=utf-8"
print
print '''<html><head><title>Buy or rent 2013/2014</title></head><body><h1>Buy or rent 2013/2014</h1><p>This tool's purpose is to work out what it's worth to buy a house, as opposed to renting one. It presently ignores income types for your current income; all income is assumed to be salary.</p><h2>Tweak values</h2><form>
<input type="text" name="house_price" value="%0.0f" /> &lt;-- price of the house, at purchase (GBP)<br />
<input type="text" name="deposit_amount" value="%0.0f" /> &lt;-- deposit (amount of the house value that isn't in the mortgage) (GBP)<br />
<input type="text" name="rent_annual_pp" value="%0.0f" /> &lt;-- expected annual rent per person (raw GBP)<br />
<input type="text" name="rent_loss_pc" value="%0.0f" /> &lt;-- annual rent lost to repairs and so-on (%%)<br />
<input type="text" name="share_people" value="%0.0f" /> &lt;-- number of people in the house paying rent (including you)<br />
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

<h2>Simulation</h2>''' % (house_price, deposit_amount, rent_annual_pp, rent_loss_pc, share_people, rent_inflation_pc, expected_growth_pc, savings_interest_raw_pc, tax_boundary_growth_pc, mortgage_interest_pc, mortgage_years, personal_income, income_inflation_pc, years)

stamp_duty = tax.stamp_duty(house_price)
initial_outlay = stamp_duty + deposit_amount

# We run three simulations: A company, a personal business and just saving the money.
income = collections.defaultdict(lambda : 0)
outlay = collections.defaultdict(lambda : initial_outlay)
income['rent'] = initial_outlay

def out(s, v):
	if v >= 0:
		simulator.out("<p><b>%s</b>: %0.0f</p>" % (s, v))
	else:
		simulator.out("<p><b>%s</b>: <span style=\"color: red\">%0.0f</span></p>" % (s, v))

simulator.setup(('rent', 'buy'), [("Income", lambda key : int(income[key])), ("Outlay", lambda key : int(outlay[key])), ("Profit", lambda key : int(income[key] - outlay[key]))])
simulator.state("Initial purchase")
out("Initial outlay", initial_outlay)
out("Stamp duty", stamp_duty)
income['rent'] = initial_outlay
simulator.record()

for year in range(1, years+1):
	simulator.state('Year %i' % (year,))

	rent_income = rent_annual_pp * (share_people - 1)

	# Simulate a year of mortgage payments
	mortgage_interest = 0.0
	this_outlay = 0.0
	for m in range(12):
		if mortgage_size > 0:
			mortgage_interest += mortgage_size * (mortgage_month_mul - 1.0)
			mortgage_size *= mortgage_month_mul
			mortgage_size -= mortgage_payment_per_month
			this_outlay += mortgage_payment_per_month

	out("Mortgage interest", mortgage_interest)

	tax_rent = tax.total_tax(personal_income + rent_income, 0, 0, 0) - tax.total_tax(personal_income, 0, 0, 0)
	real_income = rent_income * (100 - rent_loss_pc) / 100.0 - tax_rent
	out("Rent income after tax and losses", real_income)
	if real_income > this_outlay:
		out("Rent exceeds mortgage by", real_income - this_outlay)
		income['buy'] += real_income - this_outlay
	else:
		out("Mortgage after rent income", this_outlay - real_income)
		outlay['buy'] += this_outlay - real_income

	rent_outlay = max(rent_annual_pp, this_outlay - real_income)
	outlay['rent'] += rent_outlay
	income['rent'] += rent_outlay - rent_annual_pp

	savings_interest = savings_interest_raw_pc / 100.0 * income['rent']
	tax_sav = tax.total_tax(personal_income, savings_interest, 0, 0) - tax.total_tax(personal_income, 0, 0, 0)
	out("Savings tax", tax_sav)
	income['rent'] += savings_interest - tax_sav

	# Inflate things
	rent_annual_pp *= 1.0 + rent_inflation_pc / 100.0
	personal_income *= 1.0 + income_inflation_pc / 100.0
	tax.inflate(tax_boundary_growth_pc / 100.0 + 1)
	simulator.record()

simulator.state('Post sale')
sale_price = house_price*(1.0+expected_growth_pc/100.0)**years
capital_gains = sale_price - house_price
out("Capital gains", capital_gains)
income['buy'] += sale_price - mortgage_size

simulator.record()

simulator.render()

print "</body></html>"
