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

""" Reverse diff max_flow_lp at a given snapshot """
function gradient(::typeof(max_flow_lp), dflow, model, capacities, dcapacities, hypo, dhypo, log_dist, snapshot)

    order(x, y) = x < y ? (x, y) : (y, x)

    # solver = model.solvers[snapshot]
    flow = model.flows[snapshot]
    Is, Js, Vs = [k1 for ((k1, k2), v) in flow.data], [k2 for ((k1, k2), v) in flow.data], [v for ((k1, k2), v) in flow.data]
    F = sparse(Is, Js, Vs) # sparse array from flow
    function connect!(F, transpose=false)
        for ((i, j), val) in flow.data
            F[i, j] = log_dist[i, j] # default value
            if i == 1 # gen
                if hypo[snapshot, j] == val
                    if !transpose
                        F[i, j] = Inf
                    else
                        F[j, i] = Inf
                    end
                end
                # -> schaue schnellster Weg von Start zu Ende und nehme das als Fluss/Ableitung von Start los
            elseif j == 2 # load
                if model.loads[snapshot, i] == val
                    if !transpose
                        F[i, j] = Inf
                    else
                        F[j, i] = Inf
                    end
                end
                # -> schaue schnellster Weg von Land zu Ende und nehme das als Fluss/Ableitung von Start los
            else # Leitung A -> B
                cap_i, cap_j = order(i, j)
                if isapprox(capacities[cap_i, cap_j] / exp(log_dist[cap_i, cap_j]), val) || model.net_mat[snapshot, cap_j] >= 0 # pipe full or target is already satisfied
                    F[i, j] = Inf
                end
                # -> schaue schnellster Weg von Land B zu Ende und nehme das mal (A -> B) als Fluss/Ableitung
            end
        end
    end
    connect!(F)

    # Graph to findest shortest paths
    graph1 = DiGraph(14)
    for (country, neighbors) in distances
        x = model.config.ids[country]
        for (neighbor, _) in neighbors
            y = model.config.ids[neighbor]
            add_edge!(graph1, x, y)
            add_edge!(graph1, y, x)
        end
        add_edge!(graph1, model.config.ids["start"], x)
        add_edge!(graph1, x, model.config.ids["end"])
    end

    graph2 = DiGraph(14)
    for (country, neighbors) in distances
        x = model.config.ids[country]
        for (neighbor, _) in neighbors
            y = model.config.ids[neighbor]
            add_edge!(graph2, x, y)
            add_edge!(graph2, y, x)
        end
        # Umgekehrt
        add_edge!(graph2, x, model.config.ids["start"])
        add_edge!(graph2, model.config.ids["end"], x)
    end

    # Direction 1
    res1 = dijkstra_shortest_paths(graph1, 1, F)

    # Direction 2
    res2 = dijkstra_shortest_paths(graph2, 2, F')

    # We look at pipe from i to j and see which flows change
    function propagate_forward(res1, res2, i, j, dflow)
        cap_i, cap_j = order(i, j)

        # Trace to start
        last_parent = j
        parent = i
        println("i: ", i, " j: ", j) # 6, 3
        while parent != 0
            # if i == 3
            #     println("parent: ", parent, " last_parent: ", last_parent)
            # end
            # Loss is measured by distance parent to j
            delta = dflow[parent, last_parent] / exp(res1.dists[i] + log_dist[i, j] - res1.dists[parent])
            if cap_i == 1
                dhypo[snapshot, cap_j] += delta
            else
                dcapacities[cap_i, cap_j] += delta
            end
            last_parent = parent
            parent = res1.parents[parent]
        end
        # Trace to end
        last_child = j
        child = res2.parents[j]
        while child != 0
            # if i == 3
            #     println("child: ", child, " last_child: ", last_child)
            # end
            delta = dflow[last_child, child] / exp(res2.dists[j] + log_dist[i, j] - res2.dists[child])
            if cap_i == 1
                dhypo[snapshot, cap_j] += delta
            else
                dcapacities[cap_i, cap_j] += delta
            end
            last_child = child
            child = res2.parents[child]
        end
    end

    for (country, vals) in model.config.pipes
        row = model.config.ids[country]
        for neighbor in vals
            col = model.config.ids[neighbor]
            if res2.dists[col] < Inf && res1.dists[row] < Inf # can we load from col and gen from row?
                propagate_forward(res1, res2, row, col, dflow)
            elseif res2.dists[row] < Inf && res1.dists[col] < Inf # can we load from row and gen from col?
                propagate_forward(res2, res1, col, row, dflow') # reverse roles
            end
        end
        # Hypo
        if res2.dists[row] < Inf # can we load from row?
            propagate_forward(res1, res2, 1, row, dflow) # reverse roles
        end
    end

    # dhypo[snapshot, i] += val

    return graph1, graph2, F, res1, res2
end

# r1.dists[3] + log_dist[3, 13] - r1.dists[3]
# IT, AT, ES, DK (6, 8, 9, 11)
post_dhypo = deepcopy(pre_dhypo)
post_dhypo .= 0
pre_dcapacities .= 0
g1, g2, F, r1, r2 = gradient(max_flow_lp, pre_dflows[1], model_base, t_cap, pre_dcapacities, model_base.hypothetical, post_dhypo, log.(init_mats(model_base)), 1)
r1.dists
r2.dists
r2.parents

""" Reverse diff max_flow_lp """
function gradient(::typeof(max_flow_lp), dflows, model, capacities, dcapacities, hypo, dhypo)

    log_losses = log.(init_mats(model_base))
    for snap in axes(dflows, 1)
        F, r1, r2 = gradient(max_flow_lp, dflows[snap], model, capacities, dcapacities, hypo, dhypo, log_losses, snap)
    end
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
    global pre_hypo = deepcopy(hypo)
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
costs(model_base, dict_to_named_array(cap_all, model_base.config.ids), dict_to_named_vector(shares_all, model_base.config.ids))
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