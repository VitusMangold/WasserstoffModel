using OrderedCollections
using FLoops
using Graphs
using GraphsFlows
using JLD2
using PGFPlotsX
using PrettyTables
using LaTeXStrings
using StatsPlots

include("model.jl") # Model definition and helper functions
include("costs.jl") # Cost function
include("plotting.jl")

model = load("results.jld2", "model")
model_half = load("results.jld2", "model_half")
cap_all, shares_all = load("results.jld2", "results_all")
cap_same, shares_same = load("results.jld2", "results_same")
cap_fixed, shares_fixed = load("results.jld2", "results_fixed")
cap_no_cap, shares_no_cap = load("results.jld2", "results_no_cap")
cap_nothing, shares_nothing = load("results.jld2", "results_nothing")
cap_no_cap_same, shares_no_cap_same = load("results.jld2", "results_no_cap_same")
cap_half_all, shares_half_all = load("results.jld2", "results_half_all")
cap_half_no_cap, shares_half_no_cap = load("results.jld2", "results_half_no_cap")

# Sehr interessant: shares_same > shares_no_cap, obwohl man intuitiv
# denken würde, durch Leitungen gleicht sich mehr aus -> weniger Produktion
pretty_table(
    [
        [
            "All", "Same", "Fixed", "Nothing", "No Cap", "No Cap Same"
        ] [
            costs(model, cap_all, shares_all),
            costs(model, cap_same, shares_same),
            costs(model, cap_fixed, shares_fixed),
            costs(model, cap_nothing, shares_nothing),
            costs(model, cap_no_cap, shares_no_cap),
            costs(model, cap_no_cap_same, shares_no_cap_same)
        ]
    ],
    header = ["Scenario", "Costs in €"],
    backend = Val(:latex)
)

gain = costs(model, cap_no_cap, shares_no_cap) - costs(model, cap_all, shares_all)
bc = build_costs(model, cap_all)
roi = (gain + bc) / bc

gain_half = costs(model_half, cap_half_no_cap, shares_half_no_cap) - costs(model_half, cap_half_all, shares_half_all)
bc_half = build_costs(model_half, cap_half_all)
roi_half = (gain_half + bc_half) / bc_half

pretty_table(
    [
        [
            L"5.0 €/(\operatorname{mW} \operatorname{km})", L"2.5 €/(\operatorname{mW} \operatorname{km})"
        ] [
            roi,
            roi_half
        ]
    ],
    header = ["Building costs", "Return on investment"],
    backend = Val(:latex)
)

function calc_snapshots!(snapshot, model, capacities, share_ren)
    hypo = Dict(key => value .* share_ren[key] for (key, value) in model.hypothetical)
    flows_dict = deepcopy(capacities)
    graph, mat = init_graph(model, capacities)
    set_start_end!(mat, model, hypo, snapshot)
    _, F = maximum_flow(graph, model.ids["start"], model.ids["end"], mat, DinicAlgorithm())

    # println(F[1, 3])
    # println(F[3, 1])
    for (country, neighbors) in flows_dict
        x = model.ids[country]
        for neighbor in keys(neighbors)
            y = model.ids[neighbor]
            flows_dict[country][neighbor] = F[x, y]
        end
    end
    return flows_dict
end

calc_snapshots!(1, model, cap_all, shares_all)
calc_snapshots!(4380, model, cap_all, shares_all)

pgfplotsx()
plot_shares(shares_all, shares_no_cap, ["Optimization (all)", "Optimization (without capacities)"])
savefig("optimal_shares.pdf")

plot_country(model, shares_all, "DE");
savefig("de_optimized.pdf")

# plot_country(model, shares_nothing, "DE");
# savefig("de_nothing.pdf")

# plot(model_loads["DE"][1:(31*24)]);
# plot!(model_hypothetical["DE"][1:(31*24)])