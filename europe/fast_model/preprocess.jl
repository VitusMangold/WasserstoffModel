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
    transform(_, names(_)[2:end] .=> ByRow(passmissing(x -> isnothing(x) ? missing : convert(Float64, x))), renamecols=false)    

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

# Calculate relevant indicators
renewables = [
    # "Fossil Oil",
    "Wind Offshore",
    "Solar",
    "Hydro Run-of-river and poundage",
    "Hydro Pumped Storage",
    "Wind Onshore",
    # "Fossil Hard coal",
    "Other renewable",
    # "Fossil Coal-derived gas",
    "Biomass",
    # "Fossil Gas",
    # "Fossil Brown coal/Lignite",
    # "Nuclear",
    # "Other",
    # "Waste",
    "Geothermal",
    "Hydro Water Reservoir"
]

function rename_column(col_name::String)
    # Use a regular expression to capture the part before the comma and quotes
    ma = match(r"\('([^']+)'", col_name)
    if ma !== nothing
        return ma.captures[1]  # Return the captured group
    end
    return col_name
end


function filter_consumption!(data)
    for key in keys(data)
        @pipe data[key] |>
            select!(_, (!contains).(names(_), "'Actual Consumption'")) |>
            rename!(_, rename_column.(names(_)))
    end
end

filter_consumption!(gens)

# Define a function to filter and calculate the sum of renewable energy columns
function get_renewables(df, renewables)
    renewable_columns = [colname for colname in names(df) if colname in renewables]
    return sum(eachcol(select(df, renewable_columns)))
end

function get_all_names(gens)
    all_columns = Set{String}()
    for df in values(gens)
        union!(all_columns, names(df)[2:end])
    end
    return all_columns
end

# For overview
get_all_names(gens)

# Set 0.0 if no data available
resample(x) = isempty(x) ? 0.0 : mean(x)

function resample_data(df, freq)
    sort!(df)
    df[!, "Date"] = floor.(df[!, "Date"], freq)
    result = combine(groupby(df, "Date"), names(df)[2:end] .=> (resample ∘ skipmissing), renamecols=false)
    return result
end

resample_data(gens["IT"], Hour(1))

# Get our model vectors
function calc_loads_ren(gens, loads, renewables, freq=Hour(1))
    loads = Dict(key => resample_data(value, freq)[!, "Actual Load"] for (key, value) in loads)
    renewable_sums = Dict(key => get_renewables(resample_data(gen, freq), renewables) for (key, gen) in gens)
    hypothetical = Dict(key => renewable_sums[key] .* (sum(eachcol(resample_data(gens[key], freq)[!, 2:end])) / sum(renewable_sums[key])) for key in keys(gens))
    return loads, hypothetical
end

loads, hypothetical = calc_loads_ren(gens, loads, renewables)