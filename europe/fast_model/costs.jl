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

function build_costs(model, capacities)
    sum(
        v * model.distances[country][k] for (country, value) in capacities for (k, v) in value
    ) * model.power_building_costs
end

function costs(model::MaxflowModel, capacities, share_ren)
    hypo = Dict(key => value .* share_ren[key] for (key, value) in model.hypothetical)

    # This is a thread-safe function if snapshots are disjoint
    function calc_snapshots!(snapshots)
        
        Threads.@threads for snapshot in snapshots
            # set_start_end!(mat, model, hypo, snapshot)
            # _, F = maximum_flow(graph, model.ids["start"], model.ids["end"], mat, DinicAlgorithm())
            _, F = max_flow_lp(capacities, model, hypo, snapshot)
            calc_net_flow!(model=model, flow_matrix=F, hypo=hypo, snapshot=snapshot)
        end
    end

    calc_snapshots!(eachindex(model.hypothetical["DE"]))

    gen_renewable_costs = model.power_price_renewable * sum(
        model.total_gen[key] * share_ren[key] * model.time_horizon for key in keys(model.total_gen)
    )
    net_power_costs = power_imbalance_costs(model)
    building_costs = build_costs(model, capacities)

    return gen_renewable_costs + net_power_costs + building_costs
end