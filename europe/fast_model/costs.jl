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
    return sum(net_costs.(eachcol(net_mat)[3:end])) # [3:end] is for debugging purposes
end

function build_costs(costs, distances, capacities)
    sum(capacities .* distances) * costs
end

function sum_costs(; total_gen, net_mat, share_ren, power_building_costs, p_renewable, p_overproduction, p_conventional, distances, time_horizon, capacities)
    gen_renewable_costs = (total_gen' * share_ren) * time_horizon * p_renewable
    net_power_costs = power_imbalance_costs(p_overproduction, p_conventional, net_mat, time_horizon)
    building_costs = build_costs(power_building_costs, distances, capacities)
    # println("Gen renewable costs: ", gen_renewable_costs)
    # println("Net power costs: ", net_power_costs)
    # println("Building costs: ", building_costs)
    return gen_renewable_costs + net_power_costs + building_costs
end

scale_up!(hypo, ren, share_ren) = (hypo .= ren .* share_ren'; return nothing)

function costs(model::MaxflowModel, capacities, share_ren)
    hypo = similar(model.hypothetical)
    scale_up!(hypo, model.hypothetical, share_ren)

    snapshots = axes(model.hypothetical, 1)

    # This is thread-safe if snapshots are disjoint        
    Threads.@threads for snap in snapshots
        model.flows[snap] = max_flow_lp(capacities, model, hypo, snap)
        calc_net_flow!(model.net_mat, model.loads, model.config.ids, model.flows[snap], hypo, snap)
        if snap == 1673
            # println(hypo[1, :])
            # println(model.solvers[snap])
            # println(F)
            # println(grad)
            # println("Hier")
        end
    end

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

# For backpropagation
sum_costs(
    power_building_costs,
    p_renewable,
    p_overproduction,
    p_conventional,
    time_horizon,
    total_gen,
    share_ren,
    net_mat,
    distances,
    capacities,
)::Float64 = sum_costs(
    total_gen=total_gen,
    share_ren=share_ren,
    net_mat=net_mat,
    distances=distances,
    capacities=capacities,
    power_building_costs=power_building_costs,
    p_renewable=p_renewable,
    p_overproduction=p_overproduction,
    p_conventional=p_conventional,
    time_horizon=time_horizon,
)