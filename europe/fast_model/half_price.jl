model = MaxflowModel(
    ids=Dict([["start" => 1, "end" => 2]; [key => i + 2 for (i, key) in enumerate(keys(model_loads))]]),
    hypothetical=OrderedDict(model_hypothetical),
    loads=model_loads,
    net_dict=Dict(key => zeros(length(value)) for (key, value) in model_loads),
    total_gen=Dict(key => sum(value) for (key, value) in model_hypothetical),
    distances=distances,
    time_horizon = 20, # in years
    power_building_costs = 2.5 * mw_to_kw, # in €/(mW * km), Nord-Sued-Link
    power_price_conventional = 0.20 * mw_to_kw, # in Euro/mWh
    power_price_renewable = 0.07 * mw_to_kw, # in Euro/mWh
    power_price_overproduction = 0.10 * mw_to_kw, # in Euro/mWh
)