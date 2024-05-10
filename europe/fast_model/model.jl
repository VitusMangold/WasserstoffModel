Base.@kwdef struct MaxflowModel
    ids::Dict{String, Int64}
    hypothetical::OrderedDict{String, Vector{Float64}}
    loads::Dict{String, Vector{Float64}}
    net_dict::Dict{String, Vector{Float64}} # this is just used as inplace writing buffer
    total_gen::Dict{String, Float64}
    distances::OrderedDict{String, OrderedDict{String, Float64}}
    time_horizon::Float64
    power_building_costs::Float64
    power_price_conventional::Float64
    power_price_renewable::Float64
    power_price_overproduction::Float64
end

"""Initialize the directed graph."""
function init_graph(model, capacities)
    n_nodes = length(model.ids)
    # TODO: use sparse matrix
    graph = DiGraph(n_nodes)
    capacity_matrix = zeros(n_nodes, n_nodes)

    # Iteration über die Nachbarländer jedes Landes
    for (country, neighbors) in capacities
        x = model.ids[country]
        for (neighbor, capacity) in neighbors
            y = model.ids[neighbor]
            add_edge!(graph, x, y)
            add_edge!(graph, y, x)
            capacity_matrix[x, y] = capacity
            capacity_matrix[y, x] = capacity
        end
        add_edge!(graph, model.ids["start"], x)
        add_edge!(graph, x, model.ids["end"])
    end
    return graph, capacity_matrix
end

function set_start_end!(mat, model, hypo, snapshot)
    for key in keys(model.net_dict)
        generation = hypo[key][snapshot]
        loading = model.loads[key][snapshot]
        mat[model.ids["start"], model.ids[key]] = generation
        mat[model.ids[key], model.ids["end"]] = loading
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