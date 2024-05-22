function plot_shares(shares1, shares2, label)
    lab = [first(pair) for pair in sort(collect(pairs(shares_all)), by=x->x[2], rev=true)]
    groupedbar(
        vcat([shares1[key] for key in lab], [shares2[key] for key in lab]),
        xticks = (eachindex(lab), lab),
        group=vcat(fill(label[1], length(lab)), fill(label[2], length(lab))),
        title="Optimal share of renewable energy"
    )
end

function plot_country(model, sol_shares, country, times, compare=false)
    hypo = model.hypothetical[country] * sol_shares[country]
    loads = model.loads[country]
    net = hypo - loads
    if compare
        plot(model.hypothetical[country], label="Erzeugung");
        plot!(-loads, label="Verbrauch")
        plot!(model.hypothetical[country] - loads, label="Nettoerzeugung")
        plot!(hypo, label="Optimierte Erzeugung")
        plot!(net, label="Optimierte Nettoerzeugung")
        xlims!(false, 24*14)
        tick_lab = collect(times[begin]:Day(1):times[end])
        tick = [findfirst(x-> x == month, times) for month in tick_lab]
        xticks!(tick, Dates.format.(tick_lab, "dd.mm."), xrotation=45)
        title!("Optimierte Energieerzeugung und -verbrauch für $(country)")
    else
        plot(model.hypothetical[country], label="Erzeugung");
        plot!(-loads, label="Verbrauch")
        plot!(model.hypothetical[country] - loads, label="Nettoerzeugung")
        tick_lab = collect(times[begin]:Month(1):times[end])
        tick = [findfirst(x-> x == month, times) for month in tick_lab]
        xticks!(tick, Dates.format.(tick_lab, "dd.mm."), xrotation=45)
        title!("Energieerzeugung und -verbrauch für $(country)")
    end
end