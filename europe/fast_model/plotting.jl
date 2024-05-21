function plot_shares(shares1, shares2, label)
    lab = [first(pair) for pair in sort(collect(pairs(shares_all)), by=x->x[2], rev=true)]
    groupedbar(
        vcat([shares1[key] for key in lab], [shares2[key] for key in lab]),
        xticks = (eachindex(lab), lab),
        group=vcat(fill(label[1], length(lab)), fill(label[2], length(lab))),
        title="Optimal share of renewable energy"
    )
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