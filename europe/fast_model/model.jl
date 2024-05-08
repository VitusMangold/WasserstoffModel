using DataFrames
using JSON
using Pipe
using Optim

# Parse data
data_json = JSON.parsefile("energy_data.json")
gens = data_json["generation"]
loads = data_json["loads"]

to_df(data) = @pipe data |>
    (
        k = keys(_);
        DataFrame(
            "Date" => collect(keys(first(values(_)))),
            [indicator => collect(values(_[indicator])) for indicator in k]...
        )
    ) |>
    transform(_, names(_)[2] => ByRow(passmissing(x -> isnothing(x) ? missing : convert(Float64, x))), renamecols=false)

@pipe gens["ES"] |> JSON.parse(_)
test = ...
@pipe gens["FR"] |>
    JSON.parse(_)
    

function convert_to_dfs!(data)
    for key in keys(data)
        println(key)
        data[key] = @pipe data[key] |>
            JSON.parse(_) |>
            to_df(_)
    end
    data = convert(Dict{String, DataFrame}, data)
end

convert_to_dfs!(loads)
convert_to_dfs!(gens)
loads