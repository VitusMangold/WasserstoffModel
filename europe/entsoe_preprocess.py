import pandas as pd
import matplotlib.pyplot as plt

keyFile = open('.path', 'r')
mypath = keyFile.readline().rstrip()

# df_cross_to_de = pd.read_json(mypath + "entsoe_cross_de.json")
# df_cross_to_fr = pd.read_json(mypath + "entsoe_cross_fr.json")
df_load_de = pd.read_json(mypath + "entsoe_load_de.json")
df_gen_de = pd.read_json(mypath + "entsoe_gen_de.json")
df_load_fr = pd.read_json(mypath + "entsoe_load_fr.json")
df_gen_fr = pd.read_json(mypath + "entsoe_gen_fr.json")

pd.set_option('display.max_columns', 10)
print(df_gen_de)

plt.plot(df_load_de.loc['2023-01-01':'2023-01-07'], label="Load")
# plt.plot(df_load_fr.loc['2023-01-01':'2023-01-07'])
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
print(df_gen_de["('Solar', 'Actual Aggregated')"])
df_renewable_de = df_gen_de[renewable].sum(axis=1)
print(df_gen_de.sum())
print(df_renewable_de.sum())
df_hypothetical_de = df_renewable_de * (df_gen_de.sum().sum() / df_renewable_de.sum())
plt.plot(df_renewable_de.loc['2023-01-01':'2023-01-07'], label="Renewable")
plt.plot(df_hypothetical_de.loc['2023-01-01':'2023-01-07'], label="Rescaled renewable")
plt.plot(df_gen_de.sum(axis=1).loc['2023-01-01':'2023-01-07'], label="Total Generation")
plt.legend()
plt.show()

print(df_hypothetical_de)
print(df_load_de)

df_de_net = df_hypothetical_de - df_load_de["Actual Load"]
df_fr_net = df_gen_fr.sum(axis=1) - df_load_fr["Actual Load"]
plt.plot(df_de_net.loc['2023-01-01':'2023-01-07'], label="DE: Net energy")
plt.plot(df_fr_net.loc['2023-01-01':'2023-01-07'], label="FR: Net energy")
plt.legend()
plt.show()
