import entsoe_multiple_preprocess as emp
import networkx as nx
from networkx.algorithms.flow import shortest_augmenting_path
import auto_start_end
import constants
import pandas as pd
import matplotlib.pyplot as plt

core_country = "DE"

def init_graph(capacities):
    graph = nx.DiGraph()
    net_dict = {key: pd.Series(0.0, index=loads[key].index) for key in loads}

    # Set line capacities
    for key, value in capacities.items(): # should not be DE
        graph.add_edge(core_country, key, capacity=value)
        graph.add_edge(key, core_country, capacity=value)
    return graph, net_dict  

def calculate_net_flow(flow_dict, production_per_hour, consumption_per_hour,  net_dict, snapshot):
    """ Calculate the net flow for each country given the flow."""
    # Flows from core country to other countries
    # core_to_countries = 0.0
    for key in flow_dict:
        if key not in ["Start", "Ziel"]:
            net_dict[key].iloc[snapshot] = (production_per_hour[key] - flow_dict["Start"][key]) - (consumption_per_hour[key] - flow_dict[key]["Ziel"])

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

end_time = '2023-01-07'
loads = {key: value.resample('1h').mean().loc['2023-01-01':end_time] for key, value in emp.loads.items()}
renewables = {key: value.resample('1h').mean().loc['2023-01-01':end_time] for key, value in emp.renewables.items()}
# This is the total yearly generation per country
gen_total = {key: value.loc['2023-01-01':end_time].sum().sum() for key, value in emp.gens.items()}
# These are the costs for the total yearly generation per country with the renewable power prices
gen_unscaled_costs = {key: value * constants.power_price_renewable for key, value in gen_total.items()}

def costs(capacities, share_renewables):
    """
    This is our objective function (total costs).
    """
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical = {key: renewables[key] * (gen_total[key] / renewables[key].sum()) * share_renewables[key] for key in renewables}

    # Initialize graph
    graph, net_dict = init_graph(capacities)
    # FIXME: Richtung zu DE

    for snapshot, _ in enumerate(hypothetical["DE"]):
        production_per_hour = {key: hypothetical[key].iloc[snapshot] for key in hypothetical}
        consumption_per_hour = {key: loads[key].iloc[snapshot] for key in loads}

        # Set power generation and consumption
        graph = auto_start_end.start_end_node(graph, production_per_hour, consumption_per_hour)

        _, flow_dict = nx.maximum_flow(graph, "Start", "Ziel", flow_func=shortest_augmenting_path)
        calculate_net_flow(flow_dict, production_per_hour, consumption_per_hour, net_dict, snapshot)

    gen_renewable_costs = sum(
        gen_unscaled_costs[key] * share_renewables[key] * constants.time_horizon for key, _ in gen_unscaled_costs.items()
    )
    net_power_costs = power_imbalance_costs(net_dict)
    building_costs = sum(value * constants.distances[key] for key, value in capacities.items()) * constants.power_building_costs
    
    return gen_renewable_costs + net_power_costs + building_costs

# Plot capacities
results = ({'BE': 2.27628932864678, 'CH': 5613.480849211652, 'CZ': 10135.834209017168, 'DK': 1152.3246060422075, 'FR': 23997.617462034075, 'LU': 5431.8990356233335, 'NL': 43764.21927149885, 'PL': 19735.593078375066}, {'BE': 1.007471114494228, 'CH': 1.0575945698642508, 'CZ': 1.5774695858438257, 'DE': 0.0014234443207886919, 'DK': 0.6428696374671219, 'FR': 0.9610810203137954, 'LU': 2.7549141162176634, 'NL': 1.1600210850270312, 'PL': 1.98599188940605})
graph, _ = init_graph(
    {key: int(round(value, 0)) for key, value in results[0].items()}
)
pos = {"Start": (0.5, 2), "DE": (0.5, 0), "FR": (0.2, -0.5), "PL": (1, 1), "AU": (0.75, -1), "DK": (0.4, 1),"CZ": (1,0), "CH": (0.25,-1), "NL": (0.2,0.8), "BE": (0.1,0.5), "LU": (0.1,0.25),
       "Ziel": (0.5, -2)}

# nodes
nx.draw_networkx_nodes(graph, pos, node_size=500)

# edges
for (u, v, d) in graph.edges(data=True):
    nx.draw_networkx_edges(graph, pos, edgelist=[(u, v)], width=d["capacity"]/5000)

# node labels
nx.draw_networkx_labels(graph, pos, font_size=20, font_family="sans-serif")
# edge capacity labels
edge_labels = nx.get_edge_attributes(graph, "capacity")
nx.draw_networkx_edge_labels(graph, pos, edge_labels)

ax = plt.gca()
ax.margins(0.08)
plt.axis("off")
plt.tight_layout()
plt.savefig("./presentation/termin3/capacities.pdf")
plt.show()

# Frankreich: Atom gleich lassen
# Eine Kante Fluss, Saldo positiv, Saldo negativ
# Snapshot pro Stunde: Bild des Graphen
# Tabelle: Spalte Total Erzeugung / Verbrauch
# Grafik: Graphen für alle Länder mit Kapazitäten als Kantendicken
# Kosten Ausgangszustand vs. optimiert; das auch aufgeschlüsselt
# Überproduktion vielleicht erst mal nicht belohnen
# Vielleicht erst mal für zwei Länder probieren