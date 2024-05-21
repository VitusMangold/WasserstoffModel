""" This function has to be called with the model that was used to optimize the capacities and shares!"""
function elasticities(model, capacities, share_ren)
    init = [
        model.power_building_costs,
        model.power_price_renewable,
        model.power_price_overproduction,
        model.power_price_conventional,
        model.time_horizon
    ]
    func = y -> return sum_costs(
        total_gen=model.total_gen,
        share_ren=share_ren,
        net_dict=model.net_dict, # relevant
        distances=model.distances,
        capacities=capacities, # relevant
        power_building_costs=y[1],
        p_renewable=y[2],
        p_overproduction=y[3],
        p_conventional=y[4],
        time_horizon=y[5]
    )
    return ForwardDiff.gradient(func, init) .* init ./ costs(model, capacities, share_ren) # (dy / y) / (dx / x)
    # return Enzyme.autodiff(Forward, func, Active, Duplicated(init, ones(length(init))), init)
    # autodiff(Forward, func, Duplicated, Duplicated(init, zeros(length(init))))
    # Zygote.gradient(func, init) #.* init ./ costs(model, capacities, share_ren) # (dy / y) / (dx / x)
end
elasticities(model, cap_all, shares_all)
costs(model, cap_all, shares_all)