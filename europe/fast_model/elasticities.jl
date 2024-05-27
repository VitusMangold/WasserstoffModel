
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

""" This function has to be called with the model that was used to optimize the capacities and shares!"""
function elasticities(model, capacities, share_ren)
    # init = [
    #     model.config.power_building_costs,
    #     model.config.power_price_renewable,
    #     model.config.power_price_overproduction,
    #     model.config.power_price_conventional,
    #     model.config.time_horizon
    # ]
    share_ren=dict_to_named_vector(share_ren, model.config.ids)
    capacities=dict_to_named_array(capacities, model.config.ids) # relevant
    
    # return func(init)
    # return ForwardDiff.gradient(func, init) .* init ./ costs(model, capacities, share_ren) # (dy / y) / (dx / x)

    net_mat = model.net_mat.array
    total_gen = model.total_gen.array
    share_ren_mat = share_ren.array
    distances = model.config.distances.array
    dnet_mat = Enzyme.make_zero(net_mat)
    dtotal_gen = Enzyme.make_zero(total_gen)
    dshare_ren = Enzyme.make_zero(share_ren_mat)
    ddistances = Enzyme.make_zero(distances)
    Enzyme.autodiff(Reverse, sum_costs,
        Const(model.config.power_building_costs),
        Const(model.config.power_price_renewable),
        Const(model.config.power_price_overproduction),
        Const(model.config.power_price_conventional),
        Const(model.config.time_horizon),
        Duplicated(total_gen, dtotal_gen),
        Duplicated(share_ren_mat, dshare_ren),
        Duplicated(net_mat, dnet_mat),
        Duplicated(distances, ddistances),
        Const(capacities),
    )
    return dshare_ren
    # Zygote.gradient(x -> func(x, model, capacities, share_ren), init) #.* init ./ costs(model, capacities, share_ren) # (dy / y) / (dx / x)
end
# Enzyme.API.runtimeActivity!(true)
Enzyme.API.strictAliasing!(false)
elasticities(model_base, cap_all, shares_all)

cap_all, shares_all = load("results.jld2", "results_all")
sum_costs(
    model_base.config.power_building_costs,
    model_base.config.power_price_renewable,
    model_base.config.power_price_overproduction,
    model_base.config.power_price_conventional,
    model_base.config.time_horizon,
    model_base.total_gen,
    dict_to_named_vector(shares_all, model_base.config.ids),
    model_base.net_mat,
    model_base.config.distances,
    dict_to_named_array(cap_all, model_base.config.ids),
)
x = dict_to_named_array(cap_all, model_base.config.ids), dict_to_named_vector(shares_all, model_base.config.ids)
@time costs(model_base, x...)