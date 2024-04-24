import entsoe_multiple_preprocess as emp
import networkx as nx
from networkx.algorithms.flow import shortest_augmenting_path
import auto_start_end
import constants
import pandas as pd

core_country = "DE"

# for key, item in emp.loads.items():
#     print(key)
#     print(item)

# for key, item in emp.gens.items():
#     print(key)
#     print(item)

def calculate_net_flow(flow_dict, net_dict, snapshot):
    """ Calculate the net flow for each country given the flow."""
    # Flows from core country to other countries
    core_to_countries = 0.0
    for key, value in flow_dict[core_country].items():
        if key != "Ziel":
            net_dict[key].iloc[snapshot] = value
            core_to_countries = core_to_countries + value
    # Counterpart: Accumulated flow out of core country
    net_dict[core_country].iloc[snapshot] = net_dict[core_country].iloc[snapshot] - core_to_countries
    # Flow from start to all countries
    for key, value in flow_dict["Start"].items():
        net_dict[key].iloc[snapshot] = net_dict[key].iloc[snapshot] + value
    # Flow from countries to Ziel
    for key, to_ziel in flow_dict.items():
        if key not in ["Start", "Ziel"]:
            net_dict[key].iloc[snapshot] = net_dict[key].iloc[snapshot] - to_ziel["Ziel"]


def power_imbalance_costs(net_dict):
    """ Calculate the net costs for the power imbalance. 
    We can never get a negative cost (storage intuition: can not get paid for storing more than).
    """
    def pos_reward(total):
        return -total.loc[total >= 0].sum()
    def neg_reward(total):
        return -total.loc[total < 0].sum()
    # Input is time series per country
    def net_costs(value):
        return max(
                pos_reward(value) * constants.power_price_overproduction + neg_reward(value) * constants.power_price_conventional,
                0.0
            ) * constants.time_horizon
    return sum(net_costs(value) for value in net_dict.values())

loads = {key: value.resample('1h').mean() for key, value in emp.loads.items()}
renewables = {key: value.resample('1h').mean() for key, value in emp.renewables.items()}
# This is the total yearly generation per country
gen_total = {key: value.sum().sum() for key, value in emp.gens.items()}
# These are the costs for the total yearly generation per country with the renewable power prices
gen_unscaled_costs = {key: value * constants.power_price_renewable for key, value in gen_total.items()}

def costs(capacities, share_renewables):
    """
    This is our objective function (total costs).
    """
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical = {key: renewables[key] * emp.gens[key].sum().sum() / renewables[key].sum() * share_renewables[key] for key in renewables}

    # Initialize graph
    G = nx.DiGraph()
    net_dict = {key: pd.Series(0.0, index=loads[key].index) for key in loads}

    # Set line capacities
    for key, value in capacities.items(): # should not be DE
        G.add_edge(core_country, key, capacity=value)

    for snapshot, _ in enumerate(hypothetical["DE"]):
        production_per_hour = {key: hypothetical[key].iloc[snapshot] for key in hypothetical}
        consumption_per_hour = {key: loads[key].iloc[snapshot] for key in loads}

        # Set power generation and consumption
        G = auto_start_end.start_end_node(G, production_per_hour, consumption_per_hour)

        _, flow_dict = nx.maximum_flow(G, "Start", "Ziel", flow_func=shortest_augmenting_path)
        # print(flow_dict)
        calculate_net_flow(flow_dict, net_dict, snapshot)
        # print(flow_value)
    gen_renewable_costs = sum(
        gen_unscaled_costs[key] * share_renewables[key] * constants.time_horizon for key, _ in gen_unscaled_costs.items()
    )
    net_power_costs = power_imbalance_costs(net_dict)
    building_costs = sum(value * constants.distances[key] for key, value in capacities.items()) * constants.power_building_costs
    return gen_renewable_costs + net_power_costs + building_costs

costs(
    {"BE" : 1000, "CH" : 1000, "CZ" : 1000, "DK" : 1000, "FR" : 1000, "LU" : 1000, "NL" : 1000, "PL" : 1000},
    {"BE" : 1.0, "CH" : 1.0, "CZ" : 1.0, "DE" : 1.0, "DK" : 1.0, "FR" : 1.0, "LU" : 1.0, "NL" : 1.0, "PL" : 1.0}
)
# Frankreich: Atom gleich lassen
# Eine Kante Fluss, Saldo positiv, Saldo negativ
# Snapshot pro Stunde: Bild des Graphe
# Grafik: Erzeugung/Verbrauch DE vs. alle
# Tabelle: Spalte Total Erzeugung / Verbrauch
# Grafik: Graphen für alle Länder mit Kapazitäten als Kantendicken
# Kosten Ausgangszustand vs. optimiert; das auch aufgeschlüsselt
# Überproduktion vielleicht erst mal nicht belohnen
# Vielleicht erst mal für zwei Länder probieren