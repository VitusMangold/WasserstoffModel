using OrderedCollections
using FLoops
using Graphs
using GraphsFlows
using JLD2
using PGFPlotsX
using PrettyTables
using LaTeXStrings
using StatsPlots
using ForwardDiff
using Dates

include("model.jl") # Model definition and helper functions
include("costs.jl") # Cost function
include("plotting.jl")
include("elasticities.jl")

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

build_costs(model, cap) = build_costs(model.power_building_costs, model.distances, cap)

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

times = DateTime("2023-01-01T00:00:00"):Hour(1):DateTime("2023-12-31T23:00:00")
times[1]
calc_snapshots!(1, model, cap_all, shares_all)
calc_snapshots!(6666, model, cap_all, shares_all)

pgfplotsx()
plot_shares(shares_all, shares_no_cap, ["Optimization (all)", "Optimization (without capacities)"])
savefig("optimal_shares.pdf")

plot_country(model, shares_all, "DE", times, true)
savefig("de_optimized.pdf")

plot_country(model, shares_nothing, "DE", times)
savefig("de_nothing.pdf")

pretty_table(
    [
        ["Building costs", "Power price renewable", "Power price overproduction", "Power price conventional", "Time horizon"] elasticities(model, cap_all, shares_all)
    ],
    header=["Parameter", "Cost elasticity"], backend = Val(:latex)
)

# Tatsächliche Energiekosten: Gesamtkosten durch (Anzahl der Stunden pro Jahr * Gesamterzeugung * Zeithorizont)
# # Hätte ich Leistung von 1kW: Im Jahr 1kW * 365 * 24
# actual(model, cap, share) = costs(model, cap, share) / (sum(sum(model.loads[key]) for (key, val) in share) * model.time_horizon * mw_to_kw)
actual(model, cap, share) = costs(model, cap, share) / (sum(model.total_gen[key] * val + pos_reward(model.net_dict[key]) * 0.5 - neg_reward(model.net_dict[key]) for (key, val) in share) * model.time_horizon * mw_to_kw)

actual(model, cap_all, shares_all)
actual(model, cap_no_cap, shares_no_cap)
actual(model_half, cap_half_all, shares_half_all)

costs(model, cap_all, shares_all)
costs(model, cap_no_cap, shares_no_cap)
costs(model_half, cap_half_all, shares_half_all)

pretty_table(
    [
        [
            "All", "Same", "Fixed", "Nothing", "No Cap", "No Cap Same", "Half All"
        ] [
            costs(model, cap_all, shares_all),
            costs(model, cap_same, shares_same),
            costs(model, cap_fixed, shares_fixed),
            costs(model, cap_nothing, shares_nothing),
            costs(model, cap_no_cap, shares_no_cap),
            costs(model, cap_no_cap_same, shares_no_cap_same),
            costs(model_half, cap_half_all, shares_half_all)
        ]
    ],
    header = ["Scenario", "Costs in € per kWh"],
    # backend = Val(:latex)
)

pretty_table(
    [
        [
            "All", "Same", "Fixed", "Nothing", "No Cap", "No Cap Same", "Half All"
        ] [
            actual(model, cap_all, shares_all),
            actual(model, cap_same, shares_same),
            actual(model, cap_fixed, shares_fixed),
            actual(model, cap_nothing, shares_nothing),
            actual(model, cap_no_cap, shares_no_cap),
            actual(model, cap_no_cap_same, shares_no_cap_same),
            actual(model_half, cap_half_all, shares_half_all)
        ]
    ],
    header = ["Scenario", "Costs in € per kWh"],
    # backend = Val(:latex)
)

function edge_snapshots(snapshots, model, capacities, share_ren, times, name, from, to)
    hypo = Dict(key => value .* share_ren[key] for (key, value) in model.hypothetical)

    graph, mat = init_graph(model, capacities)

    edge_DE_FR = zeros(length(snapshots))

    for (i, snapshot) in enumerate(snapshots)

        set_start_end!(mat, model, hypo, snapshot)
        _, F = maximum_flow(graph, model.ids["start"], model.ids["end"], mat, DinicAlgorithm())
        edge_DE_FR[i] = F[from, to]
    end
    ticks=1:24:(length(snapshots) + 1)
    p = plot(
        edge_DE_FR,
        title="Flow edge from $name",
        label=false,
        xticks=(ticks, Dates.format.(times[ticks], "dd")),
    )
    savefig("Edge $name.pdf")
    return p
end

# Snapshot Kante: Zwei Wochen
edge_snapshots(1:(14*24), model, cap_all, shares_all, times, "DE to FR", 6, 7)
edge_snapshots(1:(14*24), model, cap_all, shares_all, times, "DE to DK", 6, 14)