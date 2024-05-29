struct ModelConfig{S, T}
    ids::Dict{String, Int64}
    pipes::Dict{String, Vector{String}}
    distances::T
    time_horizon::S
    power_building_costs::S
    power_price_conventional::S
    power_price_renewable::S
    power_price_overproduction::S
    transport_loss::S
    function ModelConfig(;
        distances,
        time_horizon,
        power_building_costs,
        power_price_conventional,
        power_price_renewable,
        power_price_overproduction,
        transport_loss
    )
        ids = Dict([["start" => 1, "end" => 2]; [key => i + 2 for (i, key) in enumerate(keys(distances))]])
        dist = dict_to_named_array(distances, ids)
        return new{typeof(time_horizon), typeof(dist)}(
            ids,
            Dict(key => collect(keys(value)) for (key, value) in distances if !isempty(value)),
            dist,
            time_horizon,
            power_building_costs,
            power_price_conventional,
            power_price_renewable,
            power_price_overproduction,
            transport_loss
        )
    end
end

struct MaxflowModel{S, T}
    hypothetical::NamedMatrix{S, Matrix{S}, Tuple{OrderedDict{Int64, Int64}, OrderedDict{String, Int64}}}
    loads::NamedMatrix{S, Matrix{S}, Tuple{OrderedDict{Int64, Int64}, OrderedDict{String, Int64}}}
    net_mat::NamedMatrix{S, Matrix{S}, Tuple{OrderedDict{Int64, Int64}, OrderedDict{String, Int64}}} # this is just used as inplace writing buffer
    total_gen::NamedVector{S, Vector{S}, Tuple{OrderedDict{String, Int64}}}
    flows::Vector{JuMP.Containers.SparseAxisArray{Float64, 2, Tuple{Int64, Int64}}}
    solvers::Vector{Tuple{GenericModel{S}, GenericModel{S}}} # keep track of the solvers for derivatives and less init time
    config::ModelConfig{S, T}
    function MaxflowModel(;
        hypothetical,
        loads,
        config::ModelConfig{S, T}
    ) where {S, T}
        model = new{S, T}(
            net_dict_to_named_array(OrderedDict(hypothetical), config.ids),
            net_dict_to_named_array(OrderedDict(loads), config.ids),
            net_dict_to_named_array(Dict(key => zeros(length(value)) for (key, value) in loads), config.ids),
            dict_to_named_vector(Dict(key => sum(value) for (key, value) in model_hypothetical), config.ids),
            JuMP.Containers.SparseAxisArray{Float64, 2, Tuple{Int64, Int64}}[],
            Tuple{GenericModel{Float64}, GenericModel{Float64}}[],
            config
        )
        init_all_solvers!(model)
        return model
    end
end

function calc_net_flow!(net_mat, loads, ids, flow_matrix, hypo, snapshot)
    for key in axes(net_mat, 2)
        if key in [ids["start"], ids["end"]]
            continue
        end
        generation = hypo[snapshot, key]
        loading = loads[snapshot, key]
        net_mat[snapshot, key] = (
            (generation - flow_matrix[ids["start"], key]) -
            (loading - flow_matrix[key, ids["end"]])
        )
    end
    return nothing
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
    return NamedArray(mat, (names_x, names_y))
end

function dict_to_named_vector(dict, ids)
    pairs = [(ids[k], v) for (k, v) in dict]
    sort!(pairs, by=x->x[1])
    vals = vcat(zeros(2), [x[2] for x in pairs])
    names = OrderedDict(
        vcat(
            ["start" => 1, "end" => 2],
            [findfirst(==(val), dict) => index + 2 for (index, val) in enumerate(vals[3:end])]
        )
    )
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
    for k in keys(net_dict)
        mat[:, k] = net_dict[k]
    end
    return mat
end