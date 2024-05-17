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