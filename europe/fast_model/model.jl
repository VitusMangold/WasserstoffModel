struct MaxflowModel
    ids::Dict{String, Int64}
    hypothetical::NamedMatrix{Float64, Matrix{Float64}, Tuple{OrderedDict{Int64, Int64}, OrderedDict{String, Int64}}}
    loads::NamedMatrix{Float64, Matrix{Float64}, Tuple{OrderedDict{Int64, Int64}, OrderedDict{String, Int64}}}
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
    ids = Dict([["start" => 1, "end" => 2]; [key => i + 2 for (i, key) in enumerate(keys(OrderedDict(loads)))]])
        model = new(
            ids,
            net_dict_to_named_array(OrderedDict(hypothetical), ids),
            net_dict_to_named_array(OrderedDict(loads), ids),
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
    for key in axes(model.net_dict, 2)
        generation = hypo[snapshot, key]
        loading = model.loads[snapshot, key]
        model.net_dict[snapshot, key] = (
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
    I = [ids[k] for (k, v) in ordered for _ in keys(v)]
    J = [ids[neighbour] for (_, v) in ordered for neighbour in keys(v)]
    V = [val for (k, v) in ordered for val in values(v)]
    mat = sparse(
        I,
        J,
        V
    )
    names_x = OrderedDict([findfirst(==(v), ids) => v for v in axes(mat, 1)])
    names_y = OrderedDict([findfirst(==(v), ids) => v for v in axes(mat, 2)])
    println(length(keys(names_x)))
    println(length(keys(names_y)))
    println(names_x)
    return NamedArray(mat, (names_x, names_y))
end

function dict_to_named_vector(dict, ids)
    vals = vcat(zeros(2), collect(values(dict)))
    names = OrderedDict([findfirst(==(v), ids) => v for v in eachindex(vals)])
    return NamedArray(
        vals,
        (names,)
    )
end

function net_dict_to_named_array(net_dict, ids)
    snapshots = eachindex(last(first(net_dict)))
    init = zeros(length(snapshots), length(keys(ids)))
    names = [findfirst(==(v), ids) for v in axes(init, 2)]
    mat = NamedArray(init, (snapshots, names), ("Rows", "Cols"))
    for (k, v) in net_dict
        mat[:, k] = net_dict[k]
    end
    return mat
end