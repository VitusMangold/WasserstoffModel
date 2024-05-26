partition(iter, n_chunks) = Iterators.partition(iter, div(length(iter) + n_chunks - 1, n_chunks))

"""
Calculate the net costs for the power imbalance.
We can never get a negative cost (storage intuition: cannot get paid for storing more than).
"""
function power_imbalance_costs(p_overproduction, p_conventional, net_mat, time_horizon)
    
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
    return sum(net_costs.(eachcol(net_mat)))
end

function build_costs(costs, distances, capacities)
    sum(capacities .* distances) * costs
end

function sum_costs(; total_gen, net_mat, share_ren, power_building_costs, p_renewable, p_overproduction, p_conventional, distances, time_horizon, capacities)
    gen_renewable_costs = (total_gen' * share_ren) * time_horizon * p_renewable
    net_power_costs = power_imbalance_costs(p_overproduction, p_conventional, net_mat, time_horizon)
    building_costs = build_costs(power_building_costs, distances, capacities)
    return gen_renewable_costs + net_power_costs + building_costs
end

 function costs(model::MaxflowModel, capacities, share_ren)
    # hypo = Dict(key => value .* share_ren[key] for (key, value) in model.hypothetical)
    hypo = deepcopy(model.hypothetical) .* share_ren'

    # This is a thread-safe function if snapshots are disjoint
    function calc_snapshots!(snapshots)
        
        Threads.@threads for snapshot in snapshots
            F = max_flow_lp(capacities, model, hypo, snapshot)
            calc_net_flow!(model=model, flow_matrix=F, hypo=hypo, snapshot=snapshot)
            if snapshot == 1
                # println(F)
                # println(grad)
                # println("Hier")
            end
        end
    end

    calc_snapshots!(axes(model.hypothetical, 1))

    return sum_costs(
        total_gen=model.total_gen,
        net_mat=model.net_mat,
        power_building_costs=model.config.power_building_costs,
        p_renewable=model.config.power_price_renewable,
        p_overproduction=model.config.power_price_overproduction,
        p_conventional=model.config.power_price_conventional,
        distances=model.config.distances,
        time_horizon=model.config.time_horizon,
        share_ren=share_ren,
        capacities=capacities
    )
end