using DataFrames
using JSON
using Dates
using TimeZones
using Statistics
using Pipe
using Optim
using Plots

include("preprocess.jl")

plot(loads["ES"][1:(7*24)])
plot!(hypothetical["ES"][1:(7*24)])

