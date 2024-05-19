const mw_to_kw = 1000.0

distances = OrderedDict(
    "DE" => OrderedDict("NL" => 360, "BE" => 400, "LU" => 340, "FR" => 615, "CH" => 540, "AT" => 590, "DK" => 495, "PL" => 770, "CZ" => 355),
    "FR" => OrderedDict("ES" => 830, "IT" => 1110, "CH" => 435),
    "BE" => OrderedDict("LU" => 190, "FR" => 260),
    "IT" => OrderedDict("AT" => 760, "CH" => 690),
    "NL" => OrderedDict("BE" => 170, "DK" => 620),
    "AT" => OrderedDict("CZ" => 250),
    "CH" => OrderedDict("AT" => 680),
    "CZ" => OrderedDict("PL" => 520),
    "LU" => OrderedDict("FR" => 290),
    "ES" => OrderedDict(),
    "DK" => OrderedDict(),
    "PL" => OrderedDict(),
)

model = MaxflowModel(
    hypothetical=model_hypothetical,
    loads=model_loads,
    distances=distances,
    time_horizon = 20, # in years
    power_building_costs = 5.0 * mw_to_kw, # in €/(mW * km), Nord-Sued-Link
    power_price_conventional = 0.20 * mw_to_kw, # in Euro/mWh
    power_price_renewable = 0.07 * mw_to_kw, # in Euro/mWh
    power_price_overproduction = 0.10 * mw_to_kw, # in Euro/mWh
    transport_loss = 0.02 * 1e-3, # per km, Leckagen, Reibungsverluste, Permeation, Kompressionsverluste
)

model_half = MaxflowModel(
    hypothetical=model_hypothetical,
    loads=model_loads,
    distances=distances,
    time_horizon = 20, # in years
    power_building_costs = 2.5 * mw_to_kw, # in €/(mW * km), Nord-Sued-Link
    power_price_conventional = 0.20 * mw_to_kw, # in Euro/mWh
    power_price_renewable = 0.07 * mw_to_kw, # in Euro/mWh
    power_price_overproduction = 0.10 * mw_to_kw, # in Euro/mWh
    transport_loss = 0.02 * 1e-3, # per km, Leckagen, Reibungsverluste, Permeation, Kompressionsverluste
)