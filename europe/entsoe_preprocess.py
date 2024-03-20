import pandas as pd
import matplotlib.pyplot as plt

keyFile = open('.path', 'r')
mypath = keyFile.readline().rstrip()

# df_cross_to_de = pd.read_json(mypath + "entsoe_cross_de.json")
# df_cross_to_other = pd.read_json(mypath + "entsoe_cross_other.json")
df_load_de = pd.read_json(mypath + "entsoe_load_de.json")
df_load_de = df_load_de.tz_localize('UTC').tz_convert('Europe/Brussels')
df_gen_de = pd.read_json(mypath + "entsoe_gen_de.json")
df_gen_de = df_gen_de.tz_localize('UTC').tz_convert('Europe/Brussels')
df_load_other = pd.read_json(mypath + "entsoe_load_other.json")
df_load_other = df_load_other.tz_localize('UTC').tz_convert('Europe/Brussels')
df_gen_other = pd.read_json(mypath + "entsoe_gen_other.json")
df_gen_other = df_gen_other.tz_localize('UTC').tz_convert('Europe/Brussels')

pd.set_option('display.max_columns', 10)
print(df_gen_de)
# plt.plot(df_load_other.loc['2023-01-01':'2023-01-07'])
# plt.plot((df_gen-df_load).loc['2023-01-01':'2023-01-07'])

# Aggregated or Consumption? Nuclear? Waste?
renewable = [
    "('Biomass', 'Actual Aggregated')",
    "('Hydro Pumped Storage', 'Actual Aggregated')",
    # "('Waste', 'Actual Aggregated')",
    "('Hydro Run-of-river and poundage', 'Actual Aggregated')",
    "('Hydro Water Reservoir', 'Actual Aggregated')",
    # "('Nuclear', 'Actual Aggregated')",
    "('Solar', 'Actual Aggregated')", 
    "('Wind Offshore', 'Actual Aggregated')",
    "('Wind Offshore', 'Actual Aggregated')",
    "('Wind Onshore', 'Actual Aggregated')"
]
# print(df_gen_de["('Solar', 'Actual Aggregated')"])
renewable_de = df_gen_de[renewable].sum(axis=1)
hypothetical_de = renewable_de * (df_gen_de.sum().sum() / renewable_de.sum())
print(df_gen_de.sum())
print(renewable_de.sum())

renewable_other = df_gen_other[renewable].sum(axis=1)
hypothetical_other = renewable_other * (df_gen_other.sum().sum() / renewable_other.sum())

plt.plot(df_load_de.loc['2023-01-01':'2023-01-07'], label="Load")
plt.plot(renewable_de.loc['2023-01-01':'2023-01-07'], label="Renewable")
plt.plot(hypothetical_de.loc['2023-01-01':'2023-01-07'], label="Rescaled renewable")
plt.plot(df_gen_de.sum(axis=1).loc['2023-01-01':'2023-01-07'], label="Total Generation")
plt.legend()
plt.title("DE")
plt.show()

plt.plot(df_load_other.loc['2023-01-01':'2023-01-07'], label="Load")
plt.plot(renewable_other.loc['2023-01-01':'2023-01-07'], label="Renewable")
plt.plot(hypothetical_other.loc['2023-01-01':'2023-01-07'], label="Rescaled renewable")
plt.plot(df_gen_other.sum(axis=1).loc['2023-01-01':'2023-01-07'], label="Total Generation")
plt.legend()
plt.title("Other")
plt.show()

print(hypothetical_de)
print(df_load_de)

de_net = hypothetical_de - df_load_de["Actual Load"]
other_net = hypothetical_other - df_load_other["Actual Load"]
plt.plot(de_net.loc['2023-01-01':'2023-01-07'], label="DE: Net energy")
plt.plot(other_net.loc['2023-01-01':'2023-01-07'], label="Other country: Net energy")
plt.axhline(0, color="black")
plt.legend()
plt.show()

de_net = de_net.resample('1h').mean()
other_net = other_net.resample('1h').mean()
