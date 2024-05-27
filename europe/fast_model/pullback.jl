function ChainRulesCore.rrule(::typeof(sum_costs), model::MaxflowModel, capacities, share_ren)
    net_mat = model.net_mat.array
    share_ren_mat = share_ren.array
    dnet_mat = Enzyme.make_zero(net_mat)
    dcapacities = Enzyme.make_zero(capacities)
    dshare_ren = Enzyme.make_zero(share_ren_mat)
    Enzyme.autodiff(Reverse, sum_costs,
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

a = ChainRulesCore.rrule(sum_costs, model_base,
    dict_to_named_array(cap_all, model_base.config.ids),
    dict_to_named_vector(shares_all, model_base.config.ids)
)

function ChainRulesCore.rrule(::typeof(max_flow_lp), dnet_mat, model, dcapacities, dhypo, snapshot)
    DiffOpt.reverse_differentiate!(solver1)
    obj_exp = MOI.get.(solver1, DiffOpt.ReverseConstraintFunction(), solver[:upper])
    grad = JuMP.constant.(obj_exp)

    DiffOpt.reverse_differentiate!(solver2)
    obj_exp = MOI.get.(solver1, DiffOpt.ReverseConstraintFunction(), solver[:upper])
    grad = JuMP.constant.(obj_exp)
end

function ChainRulesCore.rrule(::typeof(costs), model::MaxflowModel, capacities, hypo)
    dnet_mat, dcapacities, dshare_ren = ChainRulesCore.rrule(sum_costs, model_base,
        dict_to_named_array(cap_all, model_base.config.ids),
        dict_to_named_vector(shares_all, model_base.config.ids)
    )
    dhypo = Enzyme.make_zero(model.hypothetical)
    # Accumulate over all snapshots
    ChainRulesCore.rrule(max_flow_lp, dnet_mat, model, dcapacities, dhypo)
    # Use dhypo??
    Enzyme.autodiff(Reverse, scale_up,
        Const(model.hypothetical),
        Duplicated(dshare_ren, dshare_ren)
    )
end