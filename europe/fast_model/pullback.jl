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
    capacities=capacities, # relevant
    power_building_costs=power_building_costs,
    p_renewable=p_renewable,
    p_overproduction=p_overproduction,
    p_conventional=p_conventional,
    time_horizon=time_horizon,
)

function ChainRulesCore.rrule(::typeof(sum_costs), model::MaxflowModel, capacities, share_ren)
    net_mat = model.net_mat.array
    share_ren_mat = share_ren.array
    dnet_mat = Enzyme.make_zero(net_mat)
    dcapacities = Enzyme.make_zero(capacities)
    dshare_ren = Enzyme.make_zero(share_ren_mat)
    Enzyme.autodiff(Reverse,
        sum_costs,
        Const(model.config.power_building_costs),
        Const(model.config.power_price_renewable),
        Const(model.config.power_price_overproduction),
        Const(model.config.power_price_conventional),
        Const(model.config.time_horizon),
        Const(model.total_gen.array),
        Duplicated(share_ren_mat, dshare_ren),
        Duplicated(net_mat, dnet_mat),
        Const(model.config.distances.array),
        Duplicated(capacities, dcapacities),
    )
    return dnet_mat, dcapacities, dshare_ren
end

function ChainRulesCore.rrule(::typeof(max_flow_lp), dflow, model, dcapacities, dhypo, snapshot)

    solver = model.solvers[snapshot]

    # Backpropagate the flow matrix impact to the achieved max flow
    MOI.set.(solver[2], DiffOpt.ReverseVariablePrimal(), solver[2][:f], dflow)
    DiffOpt.reverse_differentiate!(solver[2])
    obj_exp = MOI.get.(solver[2], DiffOpt.ReverseConstraintFunction(), solver[2][:result])
    grad = JuMP.constant.(obj_exp)

    # Backpropagate the achieved max flow to the capacities
    MOI.set(solver[1], DiffOpt.ForwardObjectiveFunction(), grad)
    DiffOpt.forward_differentiate!(solver[1])
    obj_exp = MOI.get.(solver[1], DiffOpt.ForwardConstraintFunction(), solver[1][:upper])
    grad = JuMP.constant.(obj_exp)
    return grad
end

function ChainRulesCore.rrule(::typeof(max_flow_lp), dflow, model, dcapacities, dhypo)
    for snapshot in snapshots
        ChainRulesCore.rrule(max_flow_lp, dnet_mat, model, dcapacities, dflow, snapshot)
    end
end

function ChainRulesCore.rrule(::typeof(costs), model::MaxflowModel, capacities, share_ren)
    # TODO: check that vals in inplace matrices are correct
    dnet_mat, dcapacities, dshare_ren = ChainRulesCore.rrule(
        sum_costs, model_base, capacities, share_ren
    )
    hypo = scale_up(model.hypothetical, share_ren)
    flow = model.flows
    dhypo = Enzyme.make_zero(hypo.array)
    dflow = Enzyme.make_zero(flow)

    # Use dnet_mat to backpropagate to the hypo and flow
    for snapshot in axes(model.hypothetical, 1)
        Enzyme.autodiff(Reverse, calc_net_flow!,
            Duplicated(model.net_mat.array, dnet_mat),
            Const(model.loads),
            Const(model.config.ids),
            Duplicated(flow[snapshot], dflow[snapshot]),
            Duplicated(hypo.array, dhypo),
            Const(snapshot) # snapshot
        )
    end
    # Use flow matrix to backpropagate to hypo and capacities
    # ChainRulesCore.rrule(max_flow_lp, dflow, model, dcapacities, dhypo)
    
    # Use hypo to backpropagate to shares
    Enzyme.autodiff(
        Reverse, 
        scale_up!,
        Const,
        Duplicated(hypo.array, dhypo),
        Const(model.hypothetical),
        Duplicated(share_ren.array, dshare_ren)
    )

    return dcapacities, dshare_ren
end

cap_all, shares_all = load("results.jld2", "results_all")
a = ChainRulesCore.rrule(
    costs,
    model_base,
    dict_to_named_array(cap_all, model_base.config.ids),
    dict_to_named_vector(shares_all, model_base.config.ids)
)

dh = ones(size(model_base.hypothetical))
h = deepcopy(model_base.hypothetical.array)
din = Enzyme.make_zero(dict_to_named_vector(shares_all, model_base.config.ids).array)
Enzyme.autodiff(
    Reverse,
    scale_up!,
    Const,
    Duplicated(h, dh),
    Const(model_base.hypothetical),
    Duplicated(dict_to_named_vector(shares_all, model_base.config.ids).array, din),
)

scale_up!(h, model_base.hypothetical, dict_to_named_vector(shares_all, model_base.config.ids).array)
h .= model_base.hypothetical .* dict_to_named_vector(shares_all, model_base.config.ids).array'
