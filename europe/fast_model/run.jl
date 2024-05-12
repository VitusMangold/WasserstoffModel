using DataFrames
using JSON
using Dates
using TimeZones
using Statistics
using Pipe
using FLoops
using Plots
using Graphs
using GraphsFlows
using OrderedCollections
using Optimization, OptimizationOptimJL, OptimizationNLopt

include("preprocess.jl")
include("model.jl")
include("costs.jl")

const mw_to_kw = 1000.0

distances = OrderedDict(
    "DE" => OrderedDict("NL" => 400, "BE" => 330, "LU" => 170, "FR" => 450, "CH" => 240, "AT" => 600, "DK" => 740, "PL" => 930, "CZ" => 430),
    "FR" => OrderedDict("ES" => 1050, "IT" => 1110, "CH" => 490),
    "BE" => OrderedDict("LU" => 190, "FR" => 260),
    "IT" => OrderedDict("AT" => 760, "CH" => 680),
    "NL" => OrderedDict("BE" => 170, "DK" => 620),
    "AT" => OrderedDict("CZ" => 250),
    "CH" => OrderedDict("AT" => 590),
    "CZ" => OrderedDict("PL" => 520),
    "LU" => OrderedDict("FR" => 290),
    "ES" => OrderedDict(),
    "DK" => OrderedDict(),
    "PL" => OrderedDict(),
)

model = MaxflowModel(
    ids=Dict([["start" => 1, "end" => 2]; [key => i + 2 for (i, key) in enumerate(keys(model_loads))]]),
    hypothetical=OrderedDict(model_hypothetical),
    loads=model_loads,
    net_dict=Dict(key => zeros(length(value)) for (key, value) in model_loads),
    total_gen=Dict(key => sum(value) for (key, value) in model_hypothetical),
    distances=distances,
    time_horizon = 20, # in years
    # FIXME: wieso wurde vorher gebaut?
    power_building_costs = 14.3 * mw_to_kw, # in €/(mW * km), Nord-Sued-Link
    power_price_conventional = 0.30 * mw_to_kw, # in Euro/mWh
    power_price_renewable = 0.08 * mw_to_kw, # in Euro/mWh
    power_price_overproduction = 0.10 * mw_to_kw, # in Euro/mWh
)

function count_leaves(nested_dict)
    return sum(length(sub_dict) for sub_dict in values(nested_dict))
end

function find_optimum(model; n_chunks=60)

    initial_cap = Dict(
        key => Dict(neighbor => 1000.0 for neighbor in keys(value))
        for (key, value) in model.distances
    )
    initial_share = Dict(key => 1.0 for key in keys(model.hypothetical))

    function transform(x)
        next = iterate(x)
        for (key, value) in model.distances
            for neighbor in keys(value)
                (val, state) = next
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

    # Define the cost function to be minimized; parameters are redundant for now
    cost_function = (x, p) -> costs(model, transform(x)..., n_chunks)

    lower = [[0.0 for _ in 1:count_leaves(model.distances)]; [0.0 for _ in initial_share]]
    upper = [[100000. for _ in 1:count_leaves(model.distances)]; [3.0 for _ in initial_share]]
    initial = [[1000.0 for _ in 1:count_leaves(model.distances)]; [1.0 for _ in initial_share]]

    # Optimization problem
    prob = OptimizationProblem(cost_function, initial, lb = lower, ub = upper, sense=MinSense)

    # Solution
    results = solve(prob, NLopt.LN_NELDERMEAD(), maxtime=600) # 150s
    # results = solve(prob, NLopt.LN_COBYLA, maxtime=1200) # ~ 600s stuck in local minimum
    # results = solve(prob, NLopt.LN_BOBYQA, maxtime=1200) # ~ stuck 65s in local minimum

    # Print whether the optimization was successful
    println("Optimization status: ", results.retcode)
    println("Min value: ", results.objective)

    # Extract the minimizer and transform it back if necessary
    return transform(results.u)
end

sol_cap, sol_shares = @time find_optimum(model, n_chunks=6)

function plot_shares(sol_shares)
    lab = collect(keys(sol_shares))
    bar([sol_shares[key] for key in lab], xticks = (eachindex(lab), lab), legend=false, title="Optimal share of renewable energy")
end

function plot_country(model, sol_shares, country)
    plot(model.hypothetical[country] * sol_shares[country], label="Optimized generation");
    plot!(-model.loads[country], label="Power consumption")
    plot!(model.net_dict[country], label="Net generation")
    title!("Optimal generation and consumption for $(country)")
end

plot_shares(sol_shares)
savefig("optimal_shares.png")

plot_country(model, sol_shares, "DE")

# plot(model_loads["DE"][1:(31*24)]);
# plot!(model_hypothetical["DE"][1:(31*24)])