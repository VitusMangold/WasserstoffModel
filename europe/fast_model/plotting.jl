function plot_shares(sol_shares)
    lab = collect(keys(sol_shares))
    bar([sol_shares[key] for key in lab], xticks = (eachindex(lab), lab), legend=false, title="Optimal share of renewable energy")
end

function plot_country(model, sol_shares, country)
    hypo = model.hypothetical[country] * sol_shares[country]
    loads = model.loads[country]
    net = hypo - loads
    plot(hypo, label="Optimized generation");
    plot!(-loads, label="Power consumption")
    plot!(net, label="Net generation")
    title!("Generation and consumption for $(country)")
end