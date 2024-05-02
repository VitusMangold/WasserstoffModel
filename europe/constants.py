# The time series are in MW and not in kW, it does not make a difference though
mw_to_kw = 1000.0
time_horizon = 20 * 52 # in years (52 weeks per year))
power_building_costs = 14.3 * mw_to_kw # in €/(mW * km), Nord-Sued-Link
power_price_conventional = 0.3 * mw_to_kw # in Euro/mWh
power_price_renewable = 0.08 * mw_to_kw # in Euro/mWh
power_price_overproduction = 0.10 * mw_to_kw # in Euro/mWh

distances = {
    "BE": 330,
    "CH": 290,
    "CZ": 430,
    "DK": 480,
    "FR": 450,
    "LU": 170,
    "NL": 400,
    "PL": 930,
}