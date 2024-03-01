import pypsa
import filter_ego as fe

df_line = fe.df_line_filtered.reset_index(drop=True)
df_bus = fe.df_bus_200kV.reset_index(drop=True)

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

# network.add("Generator", "My gen", bus="My bus 0", p_set=100, control="PQ")

# network.generators
# network.generators.p_set

# network.add("Load", "My load", bus="My bus 1", p_set=100)

# network.loads
# network.loads.p_set
# network.loads.q_set = 100.0
# network.pf()
# network.lines_t.p0