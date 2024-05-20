struct MaxflowModel
    ids::Dict{String, Int64}
    hypothetical::OrderedDict{String, Vector{Float64}}
    loads::Dict{String, Vector{Float64}}
    net_dict::Dict{String, Vector{Float64}} # this is just used as inplace writing buffer
    total_gen::Dict{String, Float64}
    solvers::Vector{GenericModel{Float64}} # keep track of the solvers for derivatives and less init time
    distances::OrderedDict{String, OrderedDict{String, Float64}}
    time_horizon::Float64
    power_building_costs::Float64
    power_price_conventional::Float64
    power_price_renewable::Float64
    power_price_overproduction::Float64
    transport_loss::Float64
    function MaxflowModel(;
        hypothetical,
        loads,
        distances,
        time_horizon,
        power_building_costs,
        power_price_conventional,
        power_price_renewable,
        power_price_overproduction,
        transport_loss
    )
        model = new(
            Dict([["start" => 1, "end" => 2]; [key => i + 2 for (i, key) in enumerate(keys(OrderedDict(loads)))]]),
            OrderedDict(hypothetical),
            OrderedDict(loads),
            Dict(key => zeros(length(value)) for (key, value) in loads),
            Dict(key => sum(value) for (key, value) in model_hypothetical),
            GenericModel{Float64}[],
            distances,
            time_horizon,
            power_building_costs,
            power_price_conventional,
            power_price_renewable,
            power_price_overproduction,
            transport_loss
        )
        init_all_solvers!(model)
        return model
    end
end

function calc_net_flow!(; model, flow_matrix, hypo, snapshot)
    for key in keys(model.net_dict)
        generation = hypo[key][snapshot]
        loading = model.loads[key][snapshot]
        model.net_dict[key][snapshot] = (
            (generation - flow_matrix[model.ids["start"], model.ids[key]]) -
            (loading - flow_matrix[model.ids[key], model.ids["end"]])
        )
    end
end

function count_leaves(nested_dict)
    return sum(length(sub_dict) for sub_dict in values(nested_dict))
end

function dict_to_named_array(dict, ids)
    ordered = deepcopy(OrderedDict([k => OrderedDict(subdict) for (k, subdict) in dict]))
    push!(ordered, "start" => OrderedDict())
    push!(ordered, "end" => OrderedDict())
    I = [ids[k] for (k, v) in ordered for _ in keys(v)]
    J = [ids[neighbour] for (_, v) in ordered for neighbour in keys(v)]
    V = [val for (k, v) in ordered for val in values(v)]
    mat = sparse(
        I,
        J,
        V
    )
    names_x = OrderedDict([findfirst(==(v), model.ids) => v for v in axes(mat, 1)])
    names_y = OrderedDict([findfirst(==(v), model.ids) => v for v in axes(mat, 2)])
    println(length(keys(names_x)))
    println(length(keys(names_y)))
    println(names_x)
    return NamedArray(mat, (names_x, names_y))
end
A = dict_to_named_array(model.distances, model.ids)
# NamedArray(A, (OrderedDict(ids), OrderedDict(ids)))