# pylint: disable=no-member
import pypsa
import filter_ego as fe
import pandas as pd
import geopandas as gpd
import numpy as np
from warnings import simplefilter
from shapely.geometry import Point
import math

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

def set_slack(network):
    """
    Function that chosses the bus with the maximum installed power as slack.

    Parameters
    ----------
    network : pypsa.Network object
        Container for all network components.

    Returns
    -------
    network : pypsa.Network object
        Container for all network components.

    """

    # old_slack = network.generators.index[
    #     network.generators.control == "Slack"
    # ][0]
    # # check if old slack was PV or PQ control:
    # if network.generators.p_nom[old_slack] > 50 and network.generators.carrier[
    #     old_slack
    # ] in ("solar", "wind"):
    #     old_control = "PQ"
    # elif network.generators.p_nom[
    #     old_slack
    # ] > 50 and network.generators.carrier[old_slack] not in ("solar", "wind"):
    #     old_control = "PV"
    # elif network.generators.p_nom[old_slack] < 50:
    #     old_control = "PQ"

    old_gens = network.generators
    gens_summed = network.generators_t.p.sum()
    old_gens["p_summed"] = gens_summed
    max_gen_buses_index = (
        old_gens.groupby(["bus"])
        .agg({"p_summed": "sum"})
        .p_summed.sort_values()
        .index
    )

    for bus_iter in range(1, len(max_gen_buses_index) - 1):
        if not old_gens[
            (network.generators["bus"] == max_gen_buses_index[-bus_iter])
            & (network.generators["control"] != "PQ")
        ].empty:
            new_slack_bus = max_gen_buses_index[-bus_iter]
            break

    network.generators = network.generators.drop(columns=["p_summed"])
    new_slack_gen = (
        network.generators.p_nom[
            (network.generators["bus"] == new_slack_bus)
            & (network.generators["control"] == "PV")
        ]
        .sort_values()
        .index[-1]
    )

    # network.generators.at[old_slack, "control"] = old_control
    network.generators.at[new_slack_gen, "control"] = "Slack"

# Create the date range
def get_date_range(x):
    if x is None:
        return pd.date_range('2023-01-01', periods=1, freq="YE")
    if isinstance(x, np.float64):
        return pd.date_range('2023-01-01', periods=1, freq="YE")
    assert len(x) in [8760, 17520, 26280], len(x)
    freq = (365 * 24 * 60) / len(x)
    return pd.date_range('2023-01-01', periods=len(x), freq="{}min".format(freq))

def get_rescaled_series(series):
    return series.resample('1h').mean()

# Set time points for solution
# CAUTION!!! Input is ignored if not relevant for snapshots
snapshots = pd.date_range('2023-01-01', periods=365*24, freq='h')
network.set_snapshots(snapshots)

for i, row in df_bus.iterrows():
    network.add(
        "Bus",
        "{}".format(i),
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
        "{}".format(i),
        bus0="{}".format(df_bus[df_bus["bus_id"] == row["bus0"]].index[0]),
        bus1="{}".format(df_bus[df_bus["bus_id"] == row["bus1"]].index[0]),
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
    filtered_df = df_gen_pq[df_gen_pq["generator_id"] == row["generator_id"]]
    x_p = None
    x_q = None
    if not filtered_df.empty:
        x_p = filtered_df["p_set"].iloc[0]
        x_q = filtered_df["q_set"].iloc[0]
    network.add(
        "Generator",
        "{}".format(i),
        bus="{}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        p_set=get_rescaled_series(pd.Series(x_p, index=get_date_range(x_p))),
        # q_set=get_rescaled_series(pd.Series(x_q, index=get_date_range(x_q))),
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
    filtered_df = df_load_pq[df_load_pq["load_id"] == row["load_id"]]
    x_p = None
    x_q = None
    if not filtered_df.empty:
        x_p = filtered_df["p_set"].iloc[0]
        x_q = filtered_df["q_set"].iloc[0]
    network.add(
        "Load",
        "{}".format(i),
        bus="{}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
        p_set=get_rescaled_series(pd.Series(x_p, index=get_date_range(x_p))),
        q_set=get_rescaled_series(pd.Series(x_q, index=get_date_range(x_q))),
        sign=row["sign"]
    )

print(network.loads.p_set)
print(network.loads.q_set)

for i, row in df_trans.iterrows():
    network.add(
        "Transformer",
        "{}".format(i),
        bus0="{}".format(df_bus[df_bus["bus_id"] == row["bus0"]].index[0]),
        bus1="{}".format(df_bus[df_bus["bus_id"] == row["bus1"]].index[0]),
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
        "{}".format(i),
        bus="{}".format(df_bus[df_bus["bus_id"] == row["bus"]].index[0]),
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

# def geolocation_buses(network, apply_on="grid_model"):
#     """
#     If geopandas is installed:
#     Use geometries of buses x/y(lon/lat) and polygons
#     of countries from RenpassGisParameterRegion
#     in order to locate the buses

#     Else:
#     Use coordinats of buses to locate foreign buses, which is less accurate.

#     TODO: Why not alway use geopandas??

#     Parameters
#     ----------
#     etrago : :class:`etrago.Etrago`
#        Transmission grid object
#     apply_on: str
#         State if this function is applied on the grid_model or the
#         market_model. The market_model options can only be used if the method
#         type is "market_grid".
#     """

#     transborder_lines_0 = network.lines[
#         network.lines["bus0"].isin(
#             network.buses.index[network.buses["country"] != "DE"]
#         )
#     ].index
#     transborder_lines_1 = network.lines[
#         network.lines["bus1"].isin(
#             network.buses.index[network.buses["country"] != "DE"]
#         )
#     ].index

#     # set country tag for lines
#     network.lines.loc[transborder_lines_0, "country"] = network.buses.loc[
#         network.lines.loc[transborder_lines_0, "bus0"].values, "country"
#     ].values

#     network.lines.loc[transborder_lines_1, "country"] = network.buses.loc[
#         network.lines.loc[transborder_lines_1, "bus1"].values, "country"
#     ].values
#     network.lines["country"].fillna("DE", inplace=True)
#     doubles = list(set(transborder_lines_0.intersection(transborder_lines_1)))
#     for line in doubles:
#         c_bus0 = network.buses.loc[network.lines.loc[line, "bus0"], "country"]
#         c_bus1 = network.buses.loc[network.lines.loc[line, "bus1"], "country"]
#         network.lines.loc[line, "country"] = "{}{}".format(c_bus0, c_bus1)

#     transborder_links_0 = network.links[
#         network.links["bus0"].isin(
#             network.buses.index[network.buses["country"] != "DE"]
#         )
#     ].index
#     transborder_links_1 = network.links[
#         network.links["bus1"].isin(
#             network.buses.index[network.buses["country"] != "DE"]
#         )
#     ].index

#     # set country tag for links
#     network.links.loc[transborder_links_0, "country"] = network.buses.loc[
#         network.links.loc[transborder_links_0, "bus0"].values, "country"
#     ].values

#     network.links.loc[transborder_links_1, "country"] = network.buses.loc[
#         network.links.loc[transborder_links_1, "bus1"].values, "country"
#     ].values
#     network.links["country"].fillna("DE", inplace=True)
#     doubles = list(set(transborder_links_0.intersection(transborder_links_1)))
#     for link in doubles:
#         c_bus0 = network.buses.loc[network.links.loc[link, "bus0"], "country"]
#         c_bus1 = network.buses.loc[network.links.loc[link, "bus1"], "country"]
#         network.links.loc[link, "country"] = "{}{}".format(c_bus0, c_bus1)
    
def buses_by_country(network):
    """
    Find buses of foreign countries using coordinates
    and return them as Pandas Series

    Parameters
    ----------
    self : Etrago object
        Overall container of PyPSA
    apply_on: str
        State if this function is applied on the grid_model or the
        market_model. The market_model options can only be used if the method
        type is "market_grid".

    Returns
    -------
    None
    """

    countries = {
        "Poland": "PL",
        "Czechia": "CZ",
        "Denmark": "DK",
        "Sweden": "SE",
        "Austria": "AT",
        "Switzerland": "CH",
        "Netherlands": "NL",
        "Luxembourg": "LU",
        "France": "FR",
        "Belgium": "BE",
        "United Kingdom": "GB",
        "Norway": "NO",
        "Finland": "FI",
        "Germany": "DE",
        "Russia": "RU",
    }

    # read Germany borders
    germany_sh = gpd.read_file(fe.mypath + "Germany_shapefile/de_1km.shp", crs="EPSG:3035")

    path = gpd.datasets.get_path("naturalearth_lowres")
    shapes = gpd.read_file(path)
    shapes = shapes[shapes.name.isin([*countries])].set_index(keys="name")

    # # Use Germany borders from egon-data if not using the SH test case
    # if len(germany_sh.gen.unique()) > 1:
    shapes.at["Germany", "geometry"] = germany_sh.geometry.unary_union

    geobuses = network.buses.copy()
    geobuses["geom"] = geobuses.apply(
        lambda x: Point([x["x"], x["y"]]), axis=1
    )

    geobuses = gpd.GeoDataFrame(
        data=geobuses, geometry="geom", crs="EPSG:4326"
    )
    geobuses["country"] = np.nan

    for country in countries:
        geobuses["country"][
            network.buses.index.isin(
                geobuses.clip(shapes[shapes.index == country]).index
            )
        ] = countries[country]

    shapes = shapes.to_crs(3035)
    geobuses = geobuses.to_crs(3035)

    for bus in geobuses[geobuses["country"].isna()].index:
        distances = shapes.distance(geobuses.loc[bus, "geom"])
        closest = distances.idxmin()
        geobuses.loc[bus, "country"] = countries[closest]

    network.buses = geobuses.drop(columns="geom")
    
def set_q_national_loads(network, cos_phi):
    """
    Set q component of national loads based on the p component and cos_phi

    Parameters
    ----------
    network : :class:`pypsa.Network`
        Overall container of PyPSA
    cos_phi : float
        Choose ration of active and reactive power of foreign loads

    Returns
    -------
    network : :class:`pypsa.Network`
        Overall container of PyPSA

    """

    national_buses = network.buses[
        (network.buses.country == "DE") & (network.buses.carrier == "AC")
    ]

    # Calculate q national loads based on p and cos_phi
    new_q_loads = network.loads_t["p_set"].loc[
        :,
        network.loads.index[
            (network.loads.bus.astype(str).isin(national_buses.index))
            & (network.loads.carrier.astype(str) == "AC")
        ],
    ] * math.tan(math.acos(cos_phi))

    # insert the calculated q in loads_t. Only loads without previous
    # assignment are affected
    network.loads_t.q_set = pd.merge(
        network.loads_t.q_set,
        new_q_loads,
        how="inner",
        right_index=True,
        left_index=True,
        suffixes=("", "delete_"),
    )
    network.loads_t.q_set.drop(
        [i for i in network.loads_t.q_set.columns if "delete" in i],
        axis=1,
        inplace=True,
    )


def set_q_foreign_loads(network, cos_phi):
    """Set reative power timeseries of loads in neighbouring countries

    Parameters
    ----------
    etrago : :class:`etrago.Etrago
        Transmission grid object
    cos_phi: float
        Choose ration of active and reactive power of foreign loads

    Returns
    -------
    None

    """

    foreign_buses = network.buses[
        (network.buses.country != "DE") & (network.buses.carrier == "AC")
    ]

    network.loads_t["q_set"].loc[
        :,
        network.loads.index[
            (network.loads.bus.astype(str).isin(foreign_buses.index))
            & (network.loads.carrier != "H2_for_industry")
        ].astype(int),
    ] = network.loads_t["p_set"].loc[
        :,
        network.loads.index[
            (network.loads.bus.astype(str).isin(foreign_buses.index))
            & (network.loads.carrier != "H2_for_industry")
        ],
    ].values * math.tan(
        math.acos(cos_phi)
    )

    # To avoid a problem when the index of the load is the weather year,
    # the column names were temporarily set to `int` and changed back to
    # `str`.
    network.loads_t["q_set"].columns = network.loads_t["q_set"].columns.astype(
        str
    )

# set_branch_capacity(network, {"branch_capacity_factor": {"HV": 0.5, "eHV": 0.7}})
set_slack(network)
# buses_by_country(network)
# set_q_national_loads(network, cos_phi=0.9)
# set_q_foreign_loads(network, cos_phi=0.9)

national_buses = network.buses[network.buses.carrier == "AC"]

# Calculate q loads based on p and cos_phi
cos_phi = 0.9
new_q_loads = network.loads_t["p_set"].loc[
    :,
    network.loads.index[
        (network.loads.bus.astype(str).isin(national_buses.index))
        & (network.loads.carrier.astype(str) == "AC")
    ],
] * math.tan(math.acos(cos_phi))

# insert the calculated q in loads_t. Only loads without previous
# assignment are affected
network.loads_t.q_set = pd.merge(
    network.loads_t.q_set,
    new_q_loads,
    how="inner",
    right_index=True,
    left_index=True,
    suffixes=("", "delete_"),
)
network.loads_t.q_set.drop(
    [i for i in network.loads_t.q_set.columns if "delete" in i],
    axis=1,
    inplace=True,
)

network.export_to_netcdf("/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_01.nc")



# evtl ist vieles mit network.import_series_from_dataframe leichter