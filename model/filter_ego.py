import pandas as pd
import matplotlib.pyplot as plt

mypath = "/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/"

df_bus = pd.read_csv(
    mypath + "grid__ego_pf_hv_bus/grid__ego_pf_hv_bus.csv"
)
df_line = pd.read_csv(
    mypath + "grid__ego_pf_hv_line/grid__ego_pf_hv_line.csv"
)
df_gen = pd.read_csv(
    mypath + "grid__ego_pf_hv_generator/grid__ego_pf_hv_generator.csv"
)
df_load = pd.read_csv(
    mypath + "grid__ego_pf_hv_load/grid__ego_pf_hv_load.csv"
)
# df_gen_pq = pd.read_hdf(mypath + "ego.h5") # , key='gen_pq'
pd.set_option('display.max_columns', 10)
df_gen_pq = pd.read_json(mypath + "gen_pq.json")
print(df_gen_pq.dtypes)
print(df_gen_pq)
print(df_gen_pq)

def filter_version_scn(df):
    return df.loc[(df["scn_name"] == "Status Quo") & (df["version"] == "v0.4.6")]

df_bus = filter_version_scn(df_bus)
df_line = filter_version_scn(df_line)
df_gen = filter_version_scn(df_gen)
df_load = filter_version_scn(df_load)

# filter line by >= 200kV
df_bus_200kV = df_bus.loc[df_bus['v_nom'] > 200]
bus_ids_220kV = set(df_bus_200kV['bus_id'])
# print(df_bus_200kV)
df_line_200kV = df_line[df_line['bus0'].isin(bus_ids_220kV) | df_line['bus1'].isin(bus_ids_220kV)]
# print(df_line_200kV)
# aendert nix -> gute Daten
bus_ids_220kV = set(df_line_200kV['bus0']).union(df_line_200kV['bus1'])
# print(df_bus_200kV)
df_bus_200kV = df_bus_200kV.loc[df_bus_200kV["bus_id"].isin(bus_ids_220kV)]

print(df_gen)
df_gen_200kV = df_gen.loc[df_gen["bus"].isin(bus_ids_220kV)]
print(df_gen_200kV)
gen_ids_220kV = set(df_gen_200kV['generator_id'])
df_gen_pq_200kV = df_gen_pq.loc[df_gen_pq["generator_id"].isin(gen_ids_220kV)]

# assign filtered out loads/generator to nearest bus?