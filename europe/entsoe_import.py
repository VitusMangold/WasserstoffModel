import pandas as pd
from entsoe import EntsoePandasClient

pd.set_option('display.max_columns', 10)

keyFile = open('europe/.key', 'r')
consumer_key = keyFile.readline().rstrip()

client = EntsoePandasClient(api_key=consumer_key)

start = pd.Timestamp('20230101', tz='Europe/Brussels')
end = pd.Timestamp('20240101', tz='Europe/Brussels')
country_code = 'DE'  # Germany
country_code_from = 'DE'  # Germany
country_code_to = 'FR' # France

country_code = 'DE'
df_cross_to_fr = client.query_crossborder_flows(country_code_from, country_code_to, start=start, end=end, export=True, per_hour=True)
print(df_cross_to_fr)
df_cross_to_de = client.query_crossborder_flows(country_code_to, country_code_from, start=start, end=end, export=True, per_hour=True)
print(df_cross_to_de)

df_load = client.query_load(country_code, start=start, end=end)
print(df_load)

df_gen = client.query_generation(country_code, start=start, end=end)
print(df_gen.head)

mypath = "/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/"
df_cross_to_de.to_json(mypath + "entsoe_cross_de.json")
df_cross_to_fr.to_json(mypath + "entsoe_cross_fr.json")
df_load.to_json(mypath + "entsoe_load.json")
df_gen.to_json(mypath + "entsoe_gen.json")