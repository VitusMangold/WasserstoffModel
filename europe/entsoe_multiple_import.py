import pandas as pd
from entsoe import EntsoePandasClient
import json

pd.set_option('display.max_columns', 10)

keyFile = open('europe/.key', 'r')
consumer_key = keyFile.readline().rstrip()

client = EntsoePandasClient(api_key=consumer_key)

start = pd.Timestamp('20230101', tz='Europe/Brussels')
end = pd.Timestamp('20240101', tz='Europe/Brussels')

countries = ["BE", "CH", "CZ", "DE", "DK", "FR", "LU", "NL", "PL"]
loads = {}
gens = {}

for country in countries:
    loads[country] = client.query_load(country, start=start, end=end)
    gens[country] = client.query_generation(country, start=start, end=end)

pathFile = open('.path', 'r')
mypath = pathFile.readline().rstrip()

# Convert DataFrame to JSON string and save it
def df_to_json_string(df_dict):
    return {key: df.to_json(date_format='iso') for key, df in df_dict.items()}

# Conversion
json_loads = df_to_json_string(loads)
json_gens = df_to_json_string(gens)

# Combine and save
combined_json = {'loads': json_loads, 'generation': json_gens}
with open('energy_data.json', 'w') as file:
    json.dump(combined_json, file)

# country_code = 'DE'
# df_cross_to_de = client.query_crossborder_flows(country_code_from, country_code_to, start=start, end=end, export=True, per_hour=True)
# print(df_cross_to_de)
# df_cross_to_other = client.query_crossborder_flows(country_code_to, country_code_from, start=start, end=end, export=True, per_hour=True)
# print(df_cross_to_other)
# df_cross_to_de.to_json(mypath + "entsoe_cross_de.json")
# df_cross_to_other.to_json(mypath + "entsoe_cross_other.json")
