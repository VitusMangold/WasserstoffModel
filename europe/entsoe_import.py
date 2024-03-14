import pandas as pd
from entsoe import EntsoePandasClient

pd.set_option('display.max_columns', 10)

keyFile = open('europe/.key', 'r')
consumer_key = keyFile.readline().rstrip()

client = EntsoePandasClient(api_key=consumer_key)

start = pd.Timestamp('20230101', tz='Europe/Brussels')
end = pd.Timestamp('20240101', tz='Europe/Brussels')
country_code_from = 'FR' # France
country_code_to = 'DE'  # Germany

country_code = 'DE'
df_cross_to_de = client.query_crossborder_flows(country_code_from, country_code_to, start=start, end=end, export=True, per_hour=True)
print(df_cross_to_de)
df_cross_to_fr = client.query_crossborder_flows(country_code_to, country_code_from, start=start, end=end, export=True, per_hour=True)
print(df_cross_to_fr)

df_load_de = client.query_load(country_code_from, start=start, end=end)
print(df_load_de)
df_gen_de = client.query_generation(country_code_from, start=start, end=end)
print(df_gen_de.head)

df_load_fr = client.query_load(country_code_to, start=start, end=end)
print(df_load_fr)
df_gen_fr = client.query_generation(country_code_to, start=start, end=end)
print(df_gen_fr.head)

keyFile = open('.path', 'r')
mypath = keyFile.readline().rstrip()
df_cross_to_de.to_json(mypath + "entsoe_cross_de.json")
df_cross_to_fr.to_json(mypath + "entsoe_cross_fr.json")
df_load_de.to_json(mypath + "entsoe_load_de.json")
df_gen_de.to_json(mypath + "entsoe_gen_de.json")
df_load_fr.to_json(mypath + "entsoe_load_fr.json")
df_gen_fr.to_json(mypath + "entsoe_gen_fr.json")
