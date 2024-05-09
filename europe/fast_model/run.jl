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
    ids=Dict([["start" => 1, "end" => 2]; [key => i + 2 for (i, key) in enumerate(keys(model_loads))]]),
    hypothetical=model_hypothetical,
    loads=model_loads,
    net_dict=Dict(key => zeros(length(value)) for (key, value) in model_loads),
    total_gen=Dict(key => sum(value) for (key, value) in model_hypothetical),
    distances=distances,
    time_horizon = 20 * 52, # in years (52 weeks per year))
    power_building_costs = 14.3 * mw_to_kw, # in €/(mW * km), Nord-Sued-Link
    power_price_conventional = 0.3 * mw_to_kw, # in Euro/mWh
    power_price_renewable = 0.08 * mw_to_kw, # in Euro/mWh
    power_price_overproduction = 0.10 * mw_to_kw, # in Euro/mWh
)

function count_leaves(nested_dict)
    return sum(length(sub_dict) for sub_dict in values(nested_dict))
end

function find_optimum(model)

    initial_cap = Dict(
        key => Dict(key => 1000.0 for neighbor in keys(value))
        for (key, value) in model.distances
    )
    initial_share = Dict(key => 1.0 for key in keys(model.hypothetical))

    function transform(x)
        next = iterate(x)
        for (key, value) in model.distances
            for neighbor in keys(value)
                (val, state) = next
                # println(key, neighbor, val)
                initial_cap[key][neighbor] = val
                next = iterate(x, state)
            end
        end
        for key in keys(model.hypothetical)
            (val, state) = next
            initial_share[key] = val
            next = iterate(x, state)
        end

        return initial_cap, initial_share
    end

    initial = [[1000.0 for _ in 1:count_leaves(model.distances)]; [1.0 for _ in initial_share]]
    # println(length(initial))
    # println(initial)
    result = optimize(
        x -> costs(model, transform(x)...),
        initial
    )
    return Optim.minimizer(result)
end

find_optimum(model)