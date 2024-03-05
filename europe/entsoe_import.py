import pandas as pd
from entsoe import EntsoePandasClient

keyFile = open('europe/.key', 'r')
consumer_key = keyFile.readline().rstrip()
print(consumer_key)

client = EntsoePandasClient(api_key=consumer_key)

start = pd.Timestamp('20230101', tz='Europe/Brussels')
end = pd.Timestamp('20240101', tz='Europe/Brussels')
country_code = 'DE'  # Germany
country_code_from = 'DE'  # Germany
country_code_to = 'FR' # Germany-Luxembourg
# type_marketagreement_type = 'A01'
# contract_marketagreement_type = "A01"
# process_type = 'A51'

# methods that return Pandas Series
client.query_day_ahead_prices(country_code, start=start, end=end)
client.query_net_position(country_code, start=start, end=end, dayahead=True)