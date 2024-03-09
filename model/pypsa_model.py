# pylint: disable=no-member
import pypsa
import filter_ego as fe
import pandas as pd
import numpy as np
from warnings import simplefilter

simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

# set reference coordinate system
network = pypsa.Network(crs=4326)

df_line = fe.df_line.reset_index(drop=True)
df_bus = fe.df_bus.reset_index(drop=True)
df_gen = fe.df_gen.reset_index(drop=True)
df_gen_pq = fe.df_gen_pq.reset_index(drop=True)
df_load = fe.df_load.reset_index(drop=True)
df_load_pq = fe.df_load_pq.reset_index(drop=True)
df_trans = fe.df_trans.reset_index(drop=True)
df_store = fe.df_store.reset_index(drop=True)

for df in [df_line, df_bus, df_gen, df_gen_pq, df_load, df_load_pq, df_trans, df_store]:
    for comp in [
        "Bus",
        "Line",
        "Transformer",
        "Link",
        "Load",
        "Generator",
        "Storage",
        "Store",
    ]:
        pypsa_comp = "StorageUnit" if comp == "Storage" else comp

        # Drop columns with only NaN values
        df = df.drop(df.isnull().all()[df.isnull().all()].index, axis=1)

        # Replace NaN values with defailt values from pypsa
        for c in df.columns:
            if c in network.component_attrs[pypsa_comp].index:
                df.fillna(
                    {c: network.component_attrs[pypsa_comp].default[c]},
                    inplace=True,
                )

        if pypsa_comp == "Generator":
            df.sign = 1

        # network.import_components_from_dataframe(df, pypsa_comp)

# Create the date range
def get_date_range(x):
    if x == None:
        return pd.date_range('2023-01-01', periods=1, freq="YE")
    if isinstance(x, np.float64):
        return pd.date_range('2023-01-01', periods=1, freq="YE")
    assert len(x) in [8760, 17520, 26280], len(x)
    freq = (365 * 24 * 60) / len(x)
    return pd.date_range('2023-01-01', periods=len(x), freq="{}min".format(freq))

def get_rescaled_series(series):
    return series.resample('H').sum()

# Set time points for solution
# CAUTION!!! Input is ignored if not relevant for snapshots
snapshots = pd.date_range('2023-01-01', periods=365*24, freq='h')
network.set_snapshots(snapshots)

for i, row in df_bus.iterrows():
    network.add(
        "Bus",
        "My bus {}".format(i),
        v_nom=row["v_nom"],
        carrier=row["current_type"],
        v_mag_pu_min=row["v_mag_pu_min"],
        v_mag_pu_max=row["v_mag_pu_max"],
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
        g=row["g"],
        b=row["b"],
        s_nom=row["s_nom"],
        s_nom_extendable=row["s_nom_extendable"],
        s_nom_min=row["s_nom_min"],
        s_nom_max=row["s_nom_max"],
        length=row["length"],
        terrain_factor=row["terrain_factor"],
        # ...=row["cables"],
        # ...=row["frequency"],
    )
network.lines.loc[
    network.lines.r == 0, "r"
] = 0.0001

# print(network.buses)
# print(network.lines)

print("Set gens:")
for i, row in df_gen.iterrows():
    x_p = df_gen_pq[df_gen_pq["generator_id"] == row["generator_id"]]["p_set"].iloc[0]
    x_q = df_gen_pq[df_gen_pq["generator_id"] == row["generator_id"]]["q_set"].iloc[0]
    network.add(
        "Generator",
        "My gen {}".format(i),
        bus="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        p_set=get_rescaled_series(pd.Series(x_p, index=get_date_range(x_p))),
        q_set=get_rescaled_series(pd.Series(x_q, index=get_date_range(x_q))),
        control=row["control"],
        p_nom=row["p_nom"],
        p_nom_extendable=row["p_nom_extendable"],
        p_nom_min=row["p_nom_min"],
        p_nom_max=row["p_nom_max"],
        p_min_pu=row["p_min_pu_fixed"],
        p_max_pu=row["p_max_pu_fixed"],
        sign=row["sign"],
    )

print(network.generators.p_set)

print("Set loads:")
for i, row in df_load.iterrows():
    x_p = df_load_pq[df_load_pq["load_id"] == row["load_id"]]["p_set"].iloc[0]
    x_q = df_load_pq[df_load_pq["load_id"] == row["load_id"]]["q_set"].iloc[0]
    network.add(
        "Load",
        "My load {}".format(i),
        bus="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        p_set=get_rescaled_series(pd.Series(x_p, index=get_date_range(x_p))),
        q_set=get_rescaled_series(pd.Series(x_q, index=get_date_range(x_q))),
        sign=row["sign"]
    )

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
        s_nom_extendable=row["s_nom_extendable"],
        s_nom_min=row["s_nom_min"],
        s_nom_max=row["s_nom_max"],
        tap_ratio=row["tap_ratio"],
        phase_shift=row["phase_shift"]
    )

# Set resistance of transformers
network.transformers.loc[
    network.transformers.r == 0, "r"
] = 0.0001
# Set vnom of transformers
network.transformers["v_nom"] = network.buses.loc[
    network.transformers.bus0.values, "v_nom"
].values

for i, row in df_store.iterrows():
    network.add(
        "StorageUnit",
        "My storage {}".format(i),
        bus="My bus {}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        # former_dispatch=row["dispatch"], # I think this means yes or no time-series
        control=row["control"],
        sign=row["sign"],
        p_nom=row["p_nom"],
        p_nom_extendable=row["p_nom_extendable"],
        p_nom_min=row["p_nom_min"],
        p_nom_max=row["p_nom_max"],
        p_min_pu=row["p_min_pu_fixed"],
        p_max_pu=row["p_max_pu_fixed"],
        state_of_charge_initial=row["soc_initial"],
        max_hours=row["max_hours"],
        standing_loss=row["standing_loss"],
        efficiency_store=row["efficiency_store"],
        efficiency_dispatch=row["efficiency_dispatch"],
        cyclic_state_of_charge=row["soc_cyclic"]
    )

def set_branch_capacity(network, args):
    """
    Set branch capacity factor of lines and transformers, different factors for
    HV (110kV) and eHV (220kV, 380kV).

    Parameters
    ----------
    etrago : :class:`etrago.Etrago
        Transmission grid object

    """
    # network = etrago.network
    # args = etrago.args

    network.transformers["v_nom0"] = network.transformers.bus0.map(
        network.buses.v_nom
    )

    # If any line has a time dependend s_max_pu, use the time dependend
    # factor for all lines, to avoid problems in the clustering
    if not network.lines_t.s_max_pu.empty:
        # Set time dependend s_max_pu for
        # lines without dynamic line rating to 1.0
        network.lines_t.s_max_pu[
            network.lines[
                ~network.lines.index.isin(network.lines_t.s_max_pu.columns)
            ].index
        ] = 1.0

        # Multiply time dependend s_max_pu with static branch capacitiy fator
        network.lines_t.s_max_pu[
            network.lines[network.lines.v_nom == 110].index
        ] *= args["branch_capacity_factor"]["HV"]

        network.lines_t.s_max_pu[
            network.lines[network.lines.v_nom > 110].index
        ] *= args["branch_capacity_factor"]["eHV"]
    else:
        network.lines.s_max_pu = 0.6
        # network.lines.s_max_pu[network.lines.v_nom == 110] = args[
        #     "branch_capacity_factor"
        # ]["HV"]

        # network.lines.s_max_pu[network.lines.v_nom > 110] = args[
        #     "branch_capacity_factor"
        # ]["eHV"]
    network.transformers.s_max_pu = 0.6

    # network.transformers.s_max_pu.loc[network.transformers.v_nom0 == 110] = args[
    #     "branch_capacity_factor"
    # ]["HV"]

    # network.transformers.s_max_pu.loc[network.transformers.v_nom0 > 110] = args[
    #     "branch_capacity_factor"
    # ]["eHV"]

set_branch_capacity(network, {"branch_capacity_factor": {"HV": 0.5, "eHV": 0.7}})


network.export_to_netcdf("/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_01.nc")



# evtl ist vieles mit network.import_series_from_dataframe leichter