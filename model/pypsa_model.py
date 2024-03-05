# pylint: disable=no-member
import pypsa
import filter_ego as fe
import pandas as pd
from warnings import simplefilter

simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

# evtl ist vieles mit network.import_series_from_dataframe leichter

df_line = fe.df_line.reset_index(drop=True)
df_bus = fe.df_bus.reset_index(drop=True)
df_gen = fe.df_gen.reset_index(drop=True)
df_gen_pq = fe.df_gen_pq.reset_index(drop=True)
df_load = fe.df_load.reset_index(drop=True)
df_load_pq = fe.df_load_pq.reset_index(drop=True)
df_trans = fe.df_trans.reset_index(drop=True)
df_store = fe.df_store.reset_index(drop=True)

# Create the date range
def get_date_range(x):
    if x == None:
        return pd.date_range('2023-01-01', periods=1, freq="YE")
    freq = (365 * 24 * 60) / len(x)
    return pd.date_range('2023-01-01', periods=len(x), freq="{}min".format(freq))

# truncate for debugging
# df_gen_pq['p_set'] = df_gen_pq['p_set'].apply(lambda x: pd.Series(x, index=get_date_range(x)))
# df_load_pq['p_set'] = df_load_pq['p_set'].apply(lambda x: pd.Series(x, index=get_date_range(x)))
# df_load_pq['q_set'] = df_load_pq['p_set'].apply(lambda x: pd.Series(x, index=get_date_range(x)))

# sanity check
# print("gen head")
# print(df_gen_pq.head())
# print("load head")
# print(df_load_pq.head())

# set reference coordinate system
network = pypsa.Network(crs=4326)

# set time points for solution
snapshots = pd.date_range('2023-01-01', periods=1, freq='H')
network.set_snapshots(snapshots)

for i, row in df_bus.iterrows():
    network.add(
        "Bus",
        "My bus {}".format(i),
        v_nom=row["v_nom"],
        x=row["geom"].x,
        y=row["geom"].y
    )

for i, row in df_line.iterrows():
    network.add(
        "Line",
        "My line {}".format(i),
        bus0="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus0"]].index[0]),
        bus1="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus1"]].index[0]),
        x=row["x"],
        r=row["r"],
    )

# print(network.buses)
# print(network.lines)

for i, row in df_gen.iterrows():
    x = df_gen_pq[df_gen_pq["generator_id"] == row["generator_id"]]["p_set"].iloc[0]
    network.add(
        "Generator",
        "My gen {}".format(i),
        bus="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        p_set=pd.Series(x, index=get_date_range(x)),
        control=row["control"],
        p_nom=row["p_nom"],
        p_nom_min=row["p_nom_min"],
        p_nom_max=row["p_nom_max"]
        # ...
        # dispatch
    )

# print(network.generators)
print(network.generators.p_set)

for i, row in df_load.iterrows():
    x_p = df_load_pq[df_load_pq["load_id"] == row["load_id"]]["p_set"].iloc[0]
    x_q = df_load_pq[df_load_pq["load_id"] == row["load_id"]]["q_set"].iloc[0]
    network.add(
        "Load",
        "My load {}".format(i),
        bus="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        p_set=pd.Series(x_p, index=get_date_range(x_p)),
        q_set=pd.Series(x_q, index=get_date_range(x_q)),
        sign=row["sign"]
    )

# print(network.loads)
print(network.loads.p_set)
print(network.loads.q_set)

for i, row in df_trans.iterrows():
    network.add(
        "Transformer",
        "My transformer {}".format(i),
        bus0="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus0"]].index[0]),
        bus1="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus1"]].index[0]),
        x=row["x"],
        r=row["r"],
        g=row["g"],
        b=row["b"],
        s_nom=row["s_nom"],
        # ...
    )

for i, row in df_store.iterrows():
    network.add(
        "StorageUnit",
        "My storage {}".format(i),
        bus="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        # dispatch=row["dispatch"],
        control=row["control"],
        p_nom=row["p_nom"],
        # ...
    )

network.export_to_netcdf("/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_01.nc")