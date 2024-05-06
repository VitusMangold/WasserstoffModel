# The time series are in MW and not in kW, it does not make a difference though
mw_to_kw = 1000.0
time_horizon = 20 * 52 # in years (52 weeks per year))
power_building_costs = 14.3 * mw_to_kw # in €/(mW * km), Nord-Sued-Link
power_price_conventional = 0.3 * mw_to_kw # in Euro/mWh
power_price_renewable = 0.08 * mw_to_kw # in Euro/mWh
power_price_overproduction = 0.10 * mw_to_kw # in Euro/mWh

distances = {
    "DE" : { "NL" : 400, "BE": 330, "LU": 170, "FR": 450, "CH": 240, "AT": 600, "DK": 740, "PL": 930, "CZ": 430},
    "NL" : {"BE" : 170, "DK" : 620},
    "BE" : {"LU" : 190, "FR" : 260},
    "LU": {"FR" : 290},
    "FR": {"ES" : 1050, "IT" : 1110, "CH" : 490},
    "ES" : { },
    "IT" : {"AT" : 760, "CH" : 680},
    "CH": {"AT" : 590},
    "AT" : {"CZ" : 250},
    "CZ" : {"PL" : 520},
    "PL" : { },
    "DK" : { }
}