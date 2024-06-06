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

using JuMP
using HiGHS
using DiffOpt
import MultiObjectiveAlgorithms as MOA
import MathOptInterface as MOI
using InferOpt
using Zygote
using ChainRulesCore
using NamedArrays
using SparseArrays
using Enzyme
using FLoops

using BenchmarkTools

include("model.jl") # Model definition and helper functions
include("costs.jl") # Cost function
include("preprocess.jl") # Data preprocess
include("solver.jl") # Cost function with jump
include("config.jl") # Model config used in optimization
include("optimum.jl") # Function to find the optimum

# Sanity check
[key => length(value) for (key, value) in model.hypothetical]

# Scenarios: Find optimized parameters
results_all = @time find_optimum(model_base, scenario=:all)
results_same = @time find_optimum(model_base, scenario=:same)
results_fixed = @time find_optimum(model_base, scenario=:fixed)
results_no_cap = @time find_optimum(model_base, scenario=:no_cap)
results_nothing = @time find_optimum(model_base, scenario=:nothing)
results_no_cap_fixed = @time find_optimum(model_base, scenario=:no_cap_fixed)

# Scenario with halfed building costs
results_half_all = @time find_optimum(model_half, scenario=:all)
results_half_no_cap_fixed = @time find_optimum(model_half, scenario=:no_cap_fixed)

# If you want to save just one, you can simply comment out the others
jldopen("results.jld2", "a+") do file

    file["config_base"] = model_base.config
    file["config_half"] = model_half.config

    file["results_all"] = results_all
    file["results_same"] = results_same
    file["results_fixed"] = results_fixed
    file["results_no_cap"] = results_no_cap
    file["results_nothing"] = results_nothing
    file["results_no_cap_fixed"] = results_no_cap_fixed
    file["results_half_all"] = results_half_all
    file["results_half_no_cap_fixed"] = results_half_no_cap_fixed
end