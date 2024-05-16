using DataFrames
using JSON
using Dates
using TimeZones
using Statistics
using Pipe
using FLoops
using Graphs
using GraphsFlows
using OrderedCollections
using Optimization, OptimizationOptimJL, OptimizationNLopt
using JLD2

include("model.jl") # Model definition and helper functions
include("costs.jl") # Cost function
include("preprocess.jl") # Data preprocess
include("config.jl") # Model config used in optimization
include("optimum.jl")

results_all = @time find_optimum(model, scenario=:all, n_chunks=6)
results_same = @time find_optimum(model, scenario=:same, n_chunks=6)
results_fixed = @time find_optimum(model, scenario=:fixed, n_chunks=6)
results_no_cap = @time find_optimum(model, scenario=:no_cap, n_chunks=6)
results_nothing = @time find_optimum(model, scenario=:nothing, n_chunks=6)

# If you want to save just one, you can simply comment out the others
jldopen("results.jld2", "a+") do file

    file["model"] = model

    file["results_all"] = results_all
    file["results_same"] = results_same
    file["results_fixed"] = results_fixed
    file["results_no_cap"] = results_no_cap
    file["results_nothing"] = results_nothing
end