using DataFrames
using JSON
using Dates
using TimeZones
using Pipe
using Optim

# Parse data
data_json = JSON.parsefile("energy_data.json")
gens = data_json["generation"]
loads = data_json["loads"]

function to_date(str)
    ## For ISO 8601 datetime string with UTC indicator

    # Parse the string using the correct ISO format with Z for UTC
    datetime_obj = DateTime(str, dateformat"yyyy-mm-ddTHH:MM:SS.sss\Z")

    # # Parse the string to a DateTime object using the custom format
    zoned = ZonedDateTime(datetime_obj, tz"UTC")
    return DateTime(TimeZones.astimezone(zoned, tz"Europe/Berlin"))
end

to_df(data) = @pipe data |>
    (
        k = keys(_);
        DataFrame(
            "Date" => to_date.(collect(keys(first(values(_))))),
            [indicator => collect(values(_[indicator])) for indicator in k]...
        )
    ) |>
    transform(_, names(_)[2] => ByRow(passmissing(x -> isnothing(x) ? missing : convert(Float64, x))), renamecols=false)    

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