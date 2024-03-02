import pypsa
import filter_ego as fe

# evtl ist vieles mit network.import_series_from_dataframe leichter

# df_line = fe.df_line_200kV.reset_index(drop=True)
# df_bus = fe.df_bus_200kV.reset_index(drop=True)
# df_gen = fe.df_gen_200kV.reset_index(drop=True)
# df_gen_pq = fe.df_gen_pq_200kV.reset_index(drop=True)

df_line = fe.df_line.reset_index(drop=True)
df_bus = fe.df_bus.reset_index(drop=True)
df_gen = fe.df_gen.reset_index(drop=True)
df_gen_pq = fe.df_gen_pq.reset_index(drop=True)
df_load = fe.df_load.reset_index(drop=True)
df_load_pq = fe.df_load_pq.reset_index(drop=True)
df_trans = fe.df_trans.reset_index(drop=True)
df_store = fe.df_store.reset_index(drop=True)

network = pypsa.Network()

for i, row in df_bus.iterrows():
    network.add("Bus", "My bus {}".format(i), v_nom=row["v_nom"])

for i, row in df_line.iterrows():
    network.add(
        "Line",
        "My line {}".format(i),
        bus0="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus0"]].index[0]),
        bus1="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus1"]].index[0]),
        x=row["x"],
        r=row["r"],
    )

print(network.buses)
print(network.lines)

for i, row in df_gen.iterrows():
    network.add(
        "Generator",
        "My gen {}".format(i),
        bus="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        p_set=df_gen_pq[df_gen_pq["generator_id"] == row["generator_id"]]["p_set"].iloc[0][0], # for first try, take first element
        control=row["control"]
        # dispatch
        # p_nom
        # p_nom_min
        # p_nom_max
        # ...
    )

print(network.generators)
print(network.generators.p_set)

for i, row in df_load.iterrows():
    network.add(
        "Load",
        "My load {}".format(i),
        bus="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        p_set=df_load_pq[df_load_pq["load_id"] == row["load_id"]]["p_set"].iloc[0][0], # for first try, take first element
        sign=row["sign"]
    )

print(network.loads)
# network.loads.p_set
# network.loads.q_set

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

# Simulate/solve powerflow
network.pf()
print(network.lines_t.p0)