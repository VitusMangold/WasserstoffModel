""" Reverse diff sum_costs """
function gradient(::typeof(sum_costs), model::MaxflowModel, capacities, share_ren)
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
function gradient(::typeof(set_bounds!),
    grad1, grad2, capacities, dcapacities, hypo, dhypo, model, snapshot
)
    g1 = Enzyme.make_zero(grad1)
    g2 = Enzyme.make_zero(grad2)
    Enzyme.autodiff(
        Reverse,
        set_bounds!,
        Const,
        Duplicated(g1, grad1),
        Duplicated(g2, grad2),
        Duplicated(capacities, dcapacities),
        Duplicated(hypo, dhypo),
        Const(model.loads),
        Const(model.config.pipes),
        Const(model.config.ids),
        Const(snapshot)
    )
end

""" Reverse diff max_flow_lp at a given snapshot """
function gradient(::typeof(max_flow_lp), dflow, model, snapshot)

    solver = model.solvers[snapshot]

    # Backpropagate the flow matrix impact to the achieved max flow
    MOI.set.(solver[2], DiffOpt.ReverseVariablePrimal(), solver[2][:f], dflow)
    DiffOpt.reverse_differentiate!(solver[2])
    obj_exp = MOI.get.(solver[2], DiffOpt.ReverseConstraintFunction(), solver[2][:result])
    grad = -JuMP.constant.(obj_exp) # no idea why the minus is needed here

    # Backpropagate the flow matrix impact to the capacities/hypo
    obj_exp = MOI.get.(solver[2], DiffOpt.ReverseConstraintFunction(), solver[2][:upper])
    grad2 = -JuMP.constant.(obj_exp) # no idea why the minus is needed here

    # Backpropagate the achieved max flow to the capacities/hypo
    MOI.set.(solver[1], DiffOpt.ReverseVariablePrimal(), solver[1][:f][:, 2], grad) # they have all the same gradient
    DiffOpt.reverse_differentiate!(solver[1])
    obj_exp = MOI.get.(solver[1], DiffOpt.ReverseConstraintFunction(), solver[1][:upper])
    grad1 = -JuMP.constant.(obj_exp) # no idea why the minus is NOT needed here
    return grad1, grad2
end

""" Reverse diff max_flow_lp """
function gradient(::typeof(max_flow_lp), dflows, model, capacities, dcapacities, hypo, dhypo)

    # Initialize grads
    res = gradient(max_flow_lp, dflows[1], model, 1)
    n_chunks = 8
    buffer = [[deepcopy(res) for _ in 1:n_chunks] for _ in 1:Threads.nthreads()]
    global pre_buffer = deepcopy(buffer)

    # Fill grads
    lock = ReentrantLock();
    @floop for j in 1:div(length(axes(model.hypothetical, 1)), n_chunks)
        i = Threads.threadid()
        for chunk in 1:n_chunks
            snapshot = (j - 1) * n_chunks + chunk
            grad1, grad2 = gradient(max_flow_lp, dflows[snapshot], model, snapshot)
            buffer[i][chunk] = grad1, grad2
        end
        Threads.lock(lock) do
            for chunk in 1:n_chunks
                snapshot = (j - 1) * n_chunks + chunk
                grad1, grad2 = buffer[i][chunk]
                gradient(set_bounds!,
                    grad1, grad2, capacities, dcapacities, hypo, dhypo, model, snapshot
                )
            end
        end
    end
    global post_buffer = deepcopy(buffer)
end

""" Reverse diff costs """
function gradient(::typeof(costs), model::MaxflowModel, capacities, share_ren)
    dnet_mat, dcapacities, dshare_ren = gradient(
        sum_costs, model_base, capacities, share_ren
    )
    global pre_dcapacities = deepcopy(dcapacities) # positiv -> Kosten steigen
    global pre_dshare_ren = deepcopy(dshare_ren) # positiv -> Kosten steigen
    hypo = similar(model.hypothetical)
    scale_up!(hypo, model.hypothetical, share_ren)
    flows = model.flows
    dhypo = Enzyme.make_zero(hypo.array)
    dflows = Enzyme.make_zero(flows)

    global pre_dnet_mat = deepcopy(dnet_mat) # negativ -> Kosten sinken, 0.0 weil max am Ende
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

    global pre_dhypo = deepcopy(dhypo) # wie net_mat
    global pre_dflows = deepcopy(dflows) # umgekehrt wie net_mat
    # Use flow matrix to backpropagate to hypo and capacities
    gradient(max_flow_lp, dflows, model, capacities.array, dcapacities.array, hypo.array, dhypo)
    global post_dhypo = deepcopy(dhypo) # FIXME: Sieht gut aus (-2000 falls eh Überproduktion, über -4000 hinaus, falls zu wenig?? Sollte das nicht stets mehr als -4000 sein)
    global post_dflows = deepcopy(dflows) # Ändert sich nicht -> passt

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
a = gradient(
    costs,
    model_base,
    dict_to_named_array(cap_all, model_base.config.ids),
    dict_to_named_vector(shares_all, model_base.config.ids)
)
@profview gradient(
    costs,
    model_base,
    dict_to_named_array(cap_all, model_base.config.ids),
    dict_to_named_vector(shares_all, model_base.config.ids)
)
# Test max_flow_lp diff
res = gradient(max_flow_lp, pre_dflows[1], model_base, 1)

# FIXME: Evtl. Problem: Wir haben mit nicht-stetigen Funktionen zu tun, deshalb funktioniert die Kettenregel nicht!