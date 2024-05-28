""" This function has to be called with the model that was used to optimize the capacities and shares!"""
function elasticities(model, capacities, share_ren)

    capacities=dict_to_named_array(capacities, model.config.ids)
    share_ren=dict_to_named_vector(share_ren, model.config.ids)
    costs(model, capacities, share_ren)

    # return ForwardDiff.gradient(func, init) .* init ./ costs(model, capacities, share_ren) # (dy / y) / (dx / x)

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
    return dnet_mat
    # Zygote.gradient(x -> func(x, model, capacities, share_ren), init) #.* init ./ costs(model, capacities, share_ren) # (dy / y) / (dx / x)
end
# Enzyme.API.runtimeActivity!(true)
# Enzyme.API.strictAliasing!(false)
cap_all, shares_all = load("results.jld2", "results_all")
a = elasticities(model_base, cap_all, shares_all)

cap_all, shares_all = load("results.jld2", "results_all")
x = dict_to_named_array(cap_all, model_base.config.ids), dict_to_named_vector(shares_all, model_base.config.ids)
@time costs(model_base, x...)