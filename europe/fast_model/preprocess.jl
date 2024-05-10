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
    println("Convert to DataFrame...")
    for key in keys(data)
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

function handle_missing_time(df, country, start_time, end_time, freq)
    times = start_time:freq:end_time
    for (i, time) in enumerate(times)
        if time != df[i, "Date"]
            insert!(df, i, df[i - 1, :])
            df[i, "Date"] = time
            println("Missing time point in: ", country, " ", time)
        end
    end
end

function resample_data(df, freq, country)
    sort!(df)
    df[!, "Date"] = floor.(df[!, "Date"], freq)
    result = combine(groupby(df, "Date"), names(df)[2:end] .=> (resample ∘ skipmissing), renamecols=false)
    
    start_time = DateTime("2023-01-01T00:00:00", dateformat"yyyy-mm-ddTHH:MM:SS.sss")
    end_time = DateTime("2023-12-31T23:00:00", dateformat"yyyy-mm-ddTHH:MM:SS.sss")
    handle_missing_time(result, country, start_time, end_time, freq)
    return result
end

# Get our model vectors
function calc_loads_ren(gens, loads, renewables, freq=Hour(1))
    loads = Dict(key => resample_data(value, freq, key)[!, "Actual Load"] for (key, value) in loads)
    renewable_sums = Dict(key => get_renewables(resample_data(gen, freq, key), renewables) for (key, gen) in gens)
    hypothetical = Dict(key => renewable_sums[key] * (sum(sum(eachcol(resample_data(gens[key], freq, key)[!, 2:end]))) / sum(renewable_sums[key])) for key in keys(gens))
    return loads, hypothetical
end

model_loads, model_hypothetical = calc_loads_ren(gens, loads, renewables)

# Sanity check
[key => length(value) for (key, value) in model_hypothetical]