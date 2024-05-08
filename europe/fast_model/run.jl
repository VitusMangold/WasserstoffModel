using DataFrames
using JSON
using Dates
using TimeZones
using Statistics
using Pipe
using Optim
using Plots

using Graphs
using GraphsFlows

include("preprocess.jl")
include("model.jl")
include("costs.jl")

plot(model_loads["DE"][1:(31*24)]);
plot!(model_hypothetical["DE"][1:(31*24)])

const mw_to_kw = 1000.0

distances = Dict(
    "DE" => Dict("NL" => 400, "BE" => 330, "LU" => 170, "FR" => 450, "CH" => 240, "AT" => 600, "DK" => 740, "PL" => 930, "CZ" => 430),
    "FR" => Dict("ES" => 1050, "IT" => 1110, "CH" => 490),
    "BE" => Dict("LU" => 190, "FR" => 260),
    "IT" => Dict("AT" => 760, "CH" => 680),
    "NL" => Dict("BE" => 170, "DK" => 620),
    "AT" => Dict("CZ" => 250),
    "CH" => Dict("AT" => 590),
    "CZ" => Dict("PL" => 520),
    "LU" => Dict("FR" => 290),
    "ES" => Dict(),
    "DK" => Dict(),
    "PL" => Dict(),
)

model = MaxflowModel(
    hypothetical=model_hypothetical,
    loads=model_loads,
    net_dict=Dict(key => zeros(length(value)) for (key, value) in model_loads),
    unscaled_costs=unscaled_costs,
    distances=distances, 
    time_horizon = 20 * 52, # in years (52 weeks per year))
    power_building_costs = 14.3 * mw_to_kw, # in €/(mW * km), Nord-Sued-Link
    power_price_conventional = 0.3 * mw_to_kw, # in Euro/mWh
    power_price_renewable = 0.08 * mw_to_kw, # in Euro/mWh
    power_price_overproduction = 0.10 * mw_to_kw, # in Euro/mWh
)

function find_optimum(model)

    function transform(model, x)
        share_ren = Dict(key => x[i] for (i, key) in enumerate(keys(model.hypothetical)))
        return share_ren
    end

    # initial = zeros(length(model.hypothetical)), [1.0 for _ in keys(model.hypothetical)]
    result = optimize(
        x -> costs(model, transform(model, x)...),
    )
    return Optim.minimizer(result)
end

flow_graph = Graphs.DiGraph(8)
flow_edges = [
    (1,2,10),(1,3,5),(1,4,15),(2,3,4),(2,5,9),
    (2,6,15),(3,4,4),(3,6,8),(4,7,16),(5,6,15),
    (5,8,10),(6,7,15),(6,8,10),(7,3,6),(7,8,10)
]
capacity_matrix = zeros(8, 8)
for e in flow_edges
    u, v, f = e
    Graphs.add_edge!(flow_graph, u, v)
    capacity_matrix[u,v] = f
end
f, F = maximum_flow(flow_graph, 1, 8, capacity_matrix)
F