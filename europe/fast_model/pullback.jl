""" Reverse diff sum_costs """
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

""" Reverse diff set_bounds! """
function ChainRulesCore.rrule(::typeof(set_bounds!),
    grad1, grad2, capacities, dcapacities, hypo, dhypo, model, snapshot
)
    g1 = Enzyme.make_zero(grad1)
    g2 = Enzyme.make_zero(grad2)
    Enzyme.autodiff(
        Reverse,
        set_bounds!,
        Const,
        DuplicatedNoNeed(g1, grad1),
        DuplicatedNoNeed(g2, grad2),
        Duplicated(capacities, dcapacities),
        Duplicated(hypo, dhypo),
        Const(model.loads),
        Const(model.config.pipes),
        Const(model.config.ids),
        Const(snapshot)
    )
end

""" Reverse diff max_flow_lp at a given snapshot """
function ChainRulesCore.rrule(::typeof(max_flow_lp), dflow, model, dcapacities, snapshot)

    solver = model.solvers[snapshot]

    # Backpropagate the flow matrix impact to the achieved max flow
    MOI.set.(solver[2], DiffOpt.ReverseVariablePrimal(), solver[2][:f], dflow)
    DiffOpt.reverse_differentiate!(solver[2])
    obj_exp = MOI.get.(solver[2], DiffOpt.ReverseConstraintFunction(), solver[2][:result])
    grad = JuMP.constant.(obj_exp)

    # Backpropagate the flow matrix impact to the capacities/hypo
    obj_exp = MOI.get.(solver[2], DiffOpt.ReverseConstraintFunction(), solver[2][:upper])
    grad2 = JuMP.constant.(obj_exp)

    # Backpropagate the achieved max flow to the capacities/hypo
    MOI.set.(solver[1], DiffOpt.ReverseVariablePrimal(), solver[1][:f][:, 2], grad) # they have all the same gradient
    DiffOpt.reverse_differentiate!(solver[1])
    obj_exp = MOI.get.(solver[1], DiffOpt.ReverseConstraintFunction(), solver[1][:upper])
    grad1 = JuMP.constant.(obj_exp)
    return grad1, grad2
end

""" Reverse diff max_flow_lp """
function ChainRulesCore.rrule(::typeof(max_flow_lp), dflows, model, capacities, dcapacities, hypo, dhypo)

    # Initialize grads
    res = ChainRulesCore.rrule(max_flow_lp, dflows[1], model, dcapacities, 1)
    n_chunks = 24
    buffer = [[deepcopy(res) for _ in 1:n_chunks] for _ in 1:Threads.nthreads()]

    # Fill grads
    lock = ReentrantLock();
    @floop for snapshot in 1:(axes(model.hypothetical, 1)[2] / n_chunks)
        i = Threads.threadid()
        for chunk in 1:n_chunks
            grad1, grad2 = ChainRulesCore.rrule(max_flow_lp, dflows[snapshot], model, dcapacities, snapshot)
            buffer[i][chunk] = grad1, grad2
        end
        Threads.lock(lock) do
            for chunk in 1:n_chunks
                grad1, grad2 = buffer[i][chunk]
                ChainRulesCore.rrule(set_bounds!,
                    grad1, grad2, capacities, dcapacities, hypo, dhypo, model, snapshot
                )
            end
        end
    end
end

""" Reverse diff costs """
function ChainRulesCore.rrule(::typeof(costs), model::MaxflowModel, capacities, share_ren)
    dnet_mat, dcapacities, dshare_ren = ChainRulesCore.rrule(
        sum_costs, model_base, capacities, share_ren
    )
    global pre_dcapacities = deepcopy(dcapacities)
    global pre_dshare_ren = deepcopy(dshare_ren)
    hypo = similar(model.hypothetical)
    scale_up!(hypo, model.hypothetical, share_ren)
    flows = model.flows
    dhypo = Enzyme.make_zero(hypo.array)
    dflows = Enzyme.make_zero(flows)

    # TODO: use batched autodiff
    # Use dnet_mat to backpropagate to the hypo and flow
    for snapshot in axes(model.hypothetical, 1)
        Enzyme.autodiff(Reverse, calc_net_flow!,
            Const,
            Duplicated(model.net_mat.array, dnet_mat),
            Const(model.loads),
            Const(model.config.ids),
            Duplicated(flows[snapshot], dflows[snapshot]),
            Duplicated(hypo.array, dhypo),
            Const(snapshot) # snapshot
        )
    end

    # FIXME: dcapacities is not properly updated
    # Use flow matrix to backpropagate to hypo and capacities
    ChainRulesCore.rrule(max_flow_lp, dflows, model, capacities.array, dcapacities.array, hypo.array, dhypo)
    
    # FIXME: dshares is updated too heavily
    # Use hypo to backpropagate to shares
    Enzyme.autodiff(
        Reverse,
        scale_up!,
        Const,
        Duplicated(hypo.array, dhypo),
        Const(model.hypothetical),
        Duplicated(share_ren.array, dshare_ren)
    )
    global post_dcapacities = deepcopy(dcapacities)
    global post_dshare_ren = deepcopy(dshare_ren)

    return dcapacities, dshare_ren
end

cap_all, shares_all = load("results.jld2", "results_all")
@profview costs(model_base, dict_to_named_array(cap_all, model_base.config.ids), dict_to_named_vector(shares_all, model_base.config.ids))
a = ChainRulesCore.rrule(
    costs,
    model_base,
    dict_to_named_array(cap_all, model_base.config.ids),
    dict_to_named_vector(shares_all, model_base.config.ids)
)
@profview ChainRulesCore.rrule(
    costs,
    model_base,
    dict_to_named_array(cap_all, model_base.config.ids),
    dict_to_named_vector(shares_all, model_base.config.ids)
)
@time ChainRulesCore.rrule(
    costs,
    model_base,
    dict_to_named_array(cap_all, model_base.config.ids),
    dict_to_named_vector(shares_all, model_base.config.ids)
)