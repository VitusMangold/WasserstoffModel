Base.@kwdef struct MaxflowModel
    ids::Dict{String, Int64}
    hypothetical::Dict{String, Vector{Float64}}
    loads::Dict{String, Vector{Float64}}
    unscaled_costs::Dict{String, Float64}
    distances::Dict{String, Dict{String, Float64}}
    time_horizon::Float64
    power_building_costs::Float64
    power_price_conventional::Float64
    power_price_renewable::Float64
    power_price_overproduction::Float64
end

"""Initialize the directed graph."""
function init_graph(model, capacities)
    capacity_matrix = zeros(Int, 8, 8)
    graph = DiGraph()

    # Iteration über die Nachbarländer jedes Landes
    for (country, neighbors) in capacities
        for (neighbor, capacity) in neighbors
            x = model.ids[country]
            y = model.ids[neighbor]
            add_edge!(graph, x, y)
            add_edge!(graph, y, x)
            capacity_matrix[x, y] = capacity
            capacity_matrix[y, x] = capacity
        end
    end
end

partition(iter, n_chunks) = Iterators.partition(iter, div(length(iter) + n_chunks - 1, n_chunks))