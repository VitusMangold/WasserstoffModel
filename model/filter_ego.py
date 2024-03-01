import pandas as pd

mypath = "/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/"

df_bus = pd.read_csv(
    mypath + "grid__ego_pf_hv_bus/grid__ego_pf_hv_bus.csv"
)
df_line = pd.read_csv(
    mypath + "grid__ego_pf_hv_line/grid__ego_pf_hv_line.csv"

)
print(df_bus)
print(df_line)

# filter line by >= 200kV
df_bus_200kV = df_bus.loc[(df_bus['v_nom'] > 200) & (df_bus["scn_name"] == "Status Quo") & (df_bus["version"] == "v0.4.6")]
bus_ids_220kV = set(df_bus_200kV['bus_id'])
print(df_bus_200kV)
df_line_filtered = df_line.loc[(df_line["scn_name"] == "Status Quo") & (df_line["version"] == "v0.4.6")]
df_line_filtered = df_line_filtered[df_line_filtered['bus0'].isin(bus_ids_220kV) | df_line_filtered['bus1'].isin(bus_ids_220kV)]
print(df_line_filtered)
# aendert nix -> gute Daten
bus_ids_220kV = set(df_line_filtered['bus0']).union(df_line_filtered['bus1'])
print(df_bus_200kV)
df_bus_200kV = df_bus_200kV.loc[df_bus_200kV["bus_id"].isin(bus_ids_220kV)]


# filter bus by connection to line

# assign loads/generator to nearest bus