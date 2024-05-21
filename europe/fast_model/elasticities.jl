""" This function has to be called with the model that was used to optimize the capacities and shares!"""
function elasticities(model, capacities, share_ren)
    init = [
        model.power_building_costs,
        model.power_price_renewable,
        model.power_price_overproduction,
        model.power_price_conventional,
        model.time_horizon
    ]
    share_ren=dict_to_named_vector(share_ren, model.ids)
    capacities=dict_to_named_array(capacities, model.ids) # relevant
    func = y -> return sum_costs(
        total_gen=model.total_gen,
        share_ren=share_ren,
        net_mat=model.net_mat, # relevant
        distances=model.distances,
        capacities=capacities, # relevant
        power_building_costs=y[1],
        p_renewable=y[2],
        p_overproduction=y[3],
        p_conventional=y[4],
        time_horizon=y[5]
    )
    return func(init)
    # return ForwardDiff.gradient(func, init) .* init #./ costs(model, capacities, share_ren) # (dy / y) / (dx / x)
    # return Enzyme.autodiff(Forward, func, Active, Duplicated(init, ones(length(init))), init)
    # autodiff(Forward, func, Duplicated, Duplicated(init, zeros(length(init))))
    # Zygote.gradient(func, init) #.* init ./ costs(model, capacities, share_ren) # (dy / y) / (dx / x)
end
elasticities(model, cap_all, shares_all)
dict_to_named_vector(shares_all, model.ids)
net_dict_to_named_array(model.net_dict, model.ids)[:, "DE"]
dict_to_named_array(model.distances, model.ids) .* dict_to_named_array(cap_all, model.ids)
A = dict_to_named_vector(model.total_gen, model.ids)
dict_to_named_vector(shares_all, model.ids)

typeof(net_dict_to_named_array(Dict(key => value .* shares_all[key] for (key, value) in model.hypothetical), model.ids))