import pandas as pd
from entsoe import EntsoePandasClient

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
print(df_gen)