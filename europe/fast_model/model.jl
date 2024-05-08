Base.@kwdef struct MaxflowModel
    hypothetical::Dict{String, Vector{Float64}}
    loads::Dict{String, Vector{Float64}}
    unscaled_costs::Dict{String, Float64}
    distances::Dict{String, Dict{String, Float64}}
    time_horizon::Float64
    power_building_costs::Float64
    power_price_conventional::Float64
    power_price_renewable::Float64
    power_price_overproduction::Float64
end

function costs(; model::MaxflowModel, capacities, share_ren)
    hypo = Dict(key => value .* share_ren[key] for (key, value) in keys(model.hypothetical))
    
    return 
end