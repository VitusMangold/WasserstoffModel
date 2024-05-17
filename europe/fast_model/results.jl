using OrderedCollections
using FLoops
using Graphs
using GraphsFlows
using JLD2
using Plots

include("model.jl") # Model definition and helper functions
include("costs.jl") # Cost function

model = load("results.jld2", "model")
cap_all, shares_all = load("results.jld2", "results_all")
cap_same, shares_same = load("results.jld2", "results_same")
cap_fixed, shares_fixed = load("results.jld2", "results_fixed")
cap_no_cap, shares_no_cap = load("results.jld2", "results_no_cap")
cap_nothing, shares_nothing = load("results.jld2", "results_nothing")
cap_no_cap_fixed, shares_no_cap_fixed = load("results.jld2", "results_no_cap_fixed")
cap_half_all, shares_half_all = load("results.jld2", "results_half_all")
cap_half_no_cap_fixed, shares_half_no_cap_fixed = load("results.jld2", "results_half_no_cap_fixed")

# Sehr interessant: shares_same > shares_no_cap, obwohl man intuitiv
# denken würde, durch Leitungen gleicht sich mehr aus -> weniger Produktion
costs(model, cap_all, shares_all)
costs(model, cap_same, shares_same)
costs(model, cap_fixed, shares_fixed)
costs(model, cap_nothing, shares_nothing)
costs(model, cap_no_cap_fixed, shares_no_cap_fixed)

gain = costs(model, cap_no_cap_fixed, shares_no_cap_fixed) - costs(model, cap_all, shares_all)
bc = build_costs(model, cap_all)
(gain + bc) / bc

gain = costs(model, cap_half_no_cap_fixed, shares_half_no_cap_fixed) - costs(model, cap_half_all, shares_half_all)
bc = build_costs(model, cap_half_all)
(gain + bc) / bc

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

plot_shares(shares_all)
savefig("optimal_shares.png")

plot_country(model, shares_all, "DE")

# plot(model_loads["DE"][1:(31*24)]);
# plot!(model_hypothetical["DE"][1:(31*24)])