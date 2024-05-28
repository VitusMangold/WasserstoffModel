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
    net_mat=net_mat, # relevant
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
    MOI.set(solver[1], DiffOpt.ReverseObjectiveFunction(), grad)
    DiffOpt.reverse_differentiate!(solver[1])
    obj_exp = MOI.get.(solver[1], DiffOpt.ReverseConstraintFunction(), solver[1][:upper])
    grad = JuMP.constant.(obj_exp)
    return grad
end

function ChainRulesCore.rrule(::typeof(max_flow_lp), dflow, model, dcapacities, dhypo)
    for snapshot in snapshots
        # flow = max_flow_lp(capacities, model, hypo, snapshot)
        ChainRulesCore.rrule(max_flow_lp, dnet_mat, model, dcapacities, dflow, snapshot)
    end
end

MOI.set.(solver[2], DiffOpt.ReverseVariablePrimal(), solver[2][:f], dflow)
obj_exp = MOI.get.(model_base.solvers[1][2], DiffOpt.ReverseConstraintFunction(), model_base.solvers[1][2][:upper])
grad = JuMP.constant.(obj_exp)

JuMP.coefficient.(trick, model_base.solvers[1][1][:upper])
DiffOpt.reverse_differentiate!(model_base.solvers[1][1])
obj_exp = MOI.get.(model_base.solvers[1][1], DiffOpt.ForwardConstraintFunction(), model_base.solvers[1][1][:upper])
grad = JuMP.constant.(obj_exp)

function ChainRulesCore.rrule(::typeof(costs), model::MaxflowModel, capacities, hypo)
    dnet_mat, dcapacities, dshare_ren = ChainRulesCore.rrule(
        sum_costs, model_base, capacities, hypo
    )
    dhypo = Enzyme.make_zero(model.hypothetical)
    dflow = Enzyme.make_zero(model.flow)

    # Use dnet_mat to backpropagate to the hypo and flow
    Enzyme.autodiff(Reverse, calc_net_flow!,
        Duplicated(model.net_mat.array, dnet_mat),
        Const(model.loads),
        Const(ids),
        Duplicated(flow, dflow),
        Duplicated(hypo, dhypo),
        Const(snapshot)
    )

    # Accumulate over all snapshots
    # Use flow matrix to backpropagate to hypo and capacities
    # ChainRulesCore.rrule(max_flow_lp, dflow, model, dcapacities, dhypo)

    # Use hypo to backpropagate to shares
    # Enzyme.autodiff(Reverse, scale_up,
    #     Const(model.hypothetical),
    #     Duplicated(dshare_ren, dshare_ren)
    # )
end

cap_all, shares_all = load("results.jld2", "results_all")
ChainRulesCore.rrule(
    costs,
    model_base,
    dict_to_named_array(cap_all, model_base.config.ids),
    dict_to_named_vector(shares_all, model_base.config.ids)
)