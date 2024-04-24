import pandas as pd
import matplotlib.pyplot as plt
import json
from io import StringIO
import re

# Read JSON from file
with open('energy_data.json', 'r') as file:
    data = json.load(file)

# Function to convert JSON strings back to DataFrame using StringIO
def json_string_to_df(json_dict):
    df_dict = {}
    for key, df_string in json_dict.items():
        # Wrap the JSON string with StringIO
        json_data = StringIO(df_string)
        try:
            df_dict[key] = pd.read_json(json_data).tz_convert('Europe/Brussels')
        except ValueError as e:
            print(f"Error processing key '{key}':", e)
            continue
    return df_dict

def rename_column(col_name):
    # Regex to capture the part before the comma and quotes
    match = re.match(r"\('([^']+)'", col_name)
    if match:
        return match.group(1)  # Return the captured group
    return col_name

def filter_consumption_and_rename(df_dict):
    for key, df in df_dict.items():
        filtered_columns = [col for col in df.columns if 'Actual Consumption' not in col]
        filtered_df = df[filtered_columns]
        filtered_df.columns = [rename_column(col) for col in filtered_df.columns]
        df_dict[key] = filtered_df
    return df_dict

# Conversion back to DataFrames
loads = json_string_to_df(data['loads'])
gens = json_string_to_df(data['generation'])
gens = filter_consumption_and_rename(gens)

renewable = [
    # 'Fossil Oil',
    'Wind Offshore',
    'Solar',
    'Hydro Run-of-river and poundage',
    'Hydro Pumped Storage',
    'Wind Onshore',
    # 'Fossil Hard coal',
    'Other renewable',
    # 'Fossil Coal-derived gas',
    'Biomass',
    # 'Fossil Gas',
    # 'Fossil Brown coal/Lignite',
    # 'Nuclear',
    # 'Other',
    # 'Waste',
    'Geothermal',
    'Hydro Water Reservoir'
]
def filter_for_renewables(df):
    found_renewables = [colname for colname in df.columns.values if colname in renewable]
    return df[found_renewables].sum(axis=1)
# print({key: gens[key].columns.values for key in gens})
all_columns = set()
for df in gens.values():
    all_columns.update(df.columns)
# print(all_columns)

renewables = {key: filter_for_renewables(gen) for key, gen in gens.items()}
loads = {key: value["Actual Load"] for key, value in loads.items()}
hypothetical = {key: renewables[key] * (gens[key].sum().sum() / renewables[key].sum()) for key in gens}

print(loads["DE"])
end_time = '2023-01-07'
# end_time = '2023-01-31'

# for (country, item) in loads.items():
#     plt.plot(item.loc['2023-01-01':end_time], label=country)
plt.legend()
plt.title("Energy Consumption")
# plt.show()

# for (country, item) in renewables.items():
#     plt.plot(item.loc['2023-01-01':end_time], label=country)
# plt.legend()
# plt.title("Renewable Energy Generation")
# plt.show()

for (country, item) in hypothetical.items():
    plt.plot(item.loc['2023-01-01':end_time], label=country)
plt.legend()
plt.title("Hypothetical 100% Renewable Energy Generation")
# plt.show()

end_time = '2023-01-31'
# Load vs. generation Germany
plt.show()
plt.plot(hypothetical["DE"].loc['2023-01-01':end_time], label="DE: hypothetical 100% renewables generation")
plt.plot(loads["DE"].loc['2023-01-01':end_time], label="DE: load")

# Load vs. generation Germany
sum_hypo = sum(value.resample('1h').mean() for value in hypothetical.values())
sum_loads = sum(value.resample('1h').mean() for value in loads.values())
plt.plot(sum_hypo.loc['2023-01-01':end_time], label="Sum of all countries: hypothetical 100% renewables generation")
plt.plot(sum_loads.loc['2023-01-01':end_time], label="Sum of all countries: load")
plt.legend()
plt.xticks(rotation=-20)
plt.title("Hypothetical generation vs. load")
plt.savefig("./presentation/termin3/de_sum.pdf")
plt.show()

# Net generation
net_gen_de = (hypothetical["DE"]-loads["DE"]).loc['2023-01-01':end_time]
net_gen = (sum_hypo - sum_loads).loc['2023-01-01':end_time]
print(net_gen_de)
print(net_gen)
plt.plot(net_gen_de, label="DE: hypothetical net energy")
plt.plot(net_gen, label="Sum of all countries: hypothetical net energy")
plt.legend()
plt.xticks(rotation=-20)
plt.title("Hypothetical generation minus load")
plt.savefig("./presentation/termin3/de_sum_net.pdf")
# plt.show()