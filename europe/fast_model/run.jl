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