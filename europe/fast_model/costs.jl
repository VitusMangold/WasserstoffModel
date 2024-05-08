partition(iter, n_chunks) = Iterators.partition(iter, div(length(iter) + n_chunks - 1, n_chunks))

"""
Calculate the net costs for the power imbalance.
We can never get a negative cost (storage intuition: cannot get paid for storing more than).
"""
function power_imbalance_costs(model)
    
    # Helper function to get negative rewards -> positive costs
    neg_reward(total) = -sum(x for x in total if x < 0)
    
    # Helper function to get positive rewards -> negative costs
    pos_reward(total) = -sum(x for x in total if x >= 0)
    
    # Calculate net costs for one country's time series
    function net_costs(value)
        cost = max(
            pos_reward(value) * model.power_price_overproduction +
                neg_reward(value) * model.power_price_conventional,
            0.0
        )
        return cost * model.time_horizon
    end
    
    # Sum the net costs across all countries
    return sum(net_costs(value) for value in values(model.net_dict))
end

function costs(; model::MaxflowModel, capacities, share_ren)
    hypo = Dict(key => value .* share_ren[key] for (key, value) in keys(model.hypothetical))

    # This is a thread-safe function if snapshots are disjoint
    function calc_snapshots!(snapshots)
        graph = init_graph(model, capacities)
        
        for snapshot in snapshots
            _, F = maxflow(graph, model.ids["start"], model.ids["end"], capacity_matrix)
            calc_net_flow!(model=model, flow_matrix=F, hypo=hypo, snapshot=snapshot)
        end
    end

    for part in partition(eachindex(model.hypothetical["DE"]), 12)
        calc_snapshots!(part)
    end

    gen_renewable_costs = sum(
        unscaled_costs[key] * share_renewables[key] * constants.time_horizon for key in keys(unscaled_costs)
    )
    net_power_costs = power_imbalance_costs(model)
    building_costs = sum(sum([v * value[k] for (k, v) in value]) for value in capacities.values()) * constants.power_building_costs

    return gen_renewable_costs + net_power_costs + building_costs
end