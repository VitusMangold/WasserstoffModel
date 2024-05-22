partition(iter, n_chunks) = Iterators.partition(iter, div(length(iter) + n_chunks - 1, n_chunks))

"""
Calculate the net costs for the power imbalance.
We can never get a negative cost (storage intuition: cannot get paid for storing more than).
"""
function power_imbalance_costs(p_overproduction, p_conventional, net_dict, time_horizon)
    
    # Helper function to get negative rewards -> positive costs
    neg_reward(total) = -sum(x for x in total if x < 0)
    
    # Helper function to get positive rewards -> negative costs
    pos_reward(total) = -sum(x for x in total if x >= 0)
    
    # Calculate net costs for one country's time series
    function net_costs(value)
        cost = max(
            pos_reward(value) * p_overproduction +
                neg_reward(value) * p_conventional,
            0.0
        )
        return cost * time_horizon
    end
    
    # Sum the net costs across all countries
    return sum(net_costs(value) for value in values(net_dict))
end

function build_costs(costs, distances, capacities)
    sum(
        v * distances[country][k] for (country, value) in capacities for (k, v) in value
    ) * costs
end

function sum_costs(; total_gen, net_dict, share_ren, power_building_costs, p_renewable, p_overproduction, p_conventional, distances, time_horizon, capacities)
    gen_renewable_costs = p_renewable * sum(
        total_gen[key] * share_ren[key] * time_horizon for key in keys(total_gen)
    )
    net_power_costs = power_imbalance_costs(p_overproduction, p_conventional, net_dict, time_horizon)
    building_costs = build_costs(power_building_costs, distances, capacities)
    println("gen_renewable_costs: ", gen_renewable_costs)
    println("net_power_costs: ", net_power_costs)
    println("building_costs: ", building_costs)
    return gen_renewable_costs + net_power_costs + building_costs
end

function costs(model::MaxflowModel, capacities, share_ren)
    hypo = Dict(key => value .* share_ren[key] for (key, value) in model.hypothetical)

    # This is a thread-safe function if snapshots are disjoint
    function calc_snapshots!(snapshots)
        
        Threads.@threads for snapshot in snapshots
            F = round.(max_flow_lp(capacities, model, hypo, snapshot), digits=11)
            calc_net_flow!(model=model, flow_matrix=F, hypo=hypo, snapshot=snapshot)
            if snapshot == 1902
                # println(F)
                # println(grad)
                # println("Hier")
                # global test_flow = deepcopy(F)
            end
        end
    end

    calc_snapshots!(eachindex(model.hypothetical["DE"]))

    return sum_costs(
        total_gen=model.total_gen,
        net_dict=model.net_dict,
        power_building_costs=model.power_building_costs,
        p_renewable=model.power_price_renewable,
        p_overproduction=model.power_price_overproduction,
        p_conventional=model.power_price_conventional,
        distances=model.distances,
        time_horizon=model.time_horizon,
        share_ren=share_ren,
        capacities=capacities
    )
end