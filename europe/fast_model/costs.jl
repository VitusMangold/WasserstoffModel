"""
Calculate the net costs for the power imbalance.
We can never get a negative cost (storage intuition: cannot get paid for storing more than).
"""
function power_imbalance_costs(net_dict)
    
    # Helper function to get negative rewards
    function neg_reward(total)
        return -sum(total[total .< 0])
    end
    
    # Helper function to get positive rewards
    function pos_reward(total)
        return -sum(total[total .>= 0])
    end
    
    # Calculate net costs for one country's time series
    function net_costs(value)
        cost = max(
            pos_reward(value) * constants.power_price_overproduction + neg_reward(value) * constants.power_price_conventional,
            0.0
        )
        return cost * constants.time_horizon
    end
    
    # Sum the net costs across all countries
    return sum(net_costs(value) for value in values(net_dict))
end

function costs(; model::MaxflowModel, capacities, share_ren)
    hypo = Dict(key => value .* share_ren[key] for (key, value) in keys(model.hypothetical))

    function calc_snapshots(snapshots)
        graph = init_graph(model, capacities)
        
        for snapshot in snapshots
            flow = maxflow(graph, 1, 8, capacity_matrix)
            ...
        end
    end

    for part in partition(eachindex(model.hypothetical["DE"]), 12)
        res = calc_snapshots(part)
    end

    gen_renewable_costs = sum(
        gen_unscaled_costs[key] * share_renewables[key] * constants.time_horizon for key in keys(gen_unscaled_costs)
    )
    net_power_costs = power_imbalance_costs(net_dict)
    building_costs = sum(sum([v * value[k] for (k, v) in value]) for value in capacities.values()) * constants.power_building_costs

    return gen_renewable_costs + net_power_costs + building_costs
end