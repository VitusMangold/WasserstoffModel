import entsoe_multiple_preprocess as emp
import networkx as nx
from networkx.algorithms.flow import shortest_augmenting_path
import auto_start_end

# for key, item in emp.loads.items():
#     print(key)
#     print(item)

# for key, item in emp.gens.items():
#     print(key)
#     print(item)

loads = {key: value.resample('1h').mean()["Actual Load"] for key, value in emp.loads.items()}
renewables = {key: value.resample('1h').mean() for key, value in emp.renewables.items()}
print(loads["DE"])
print(renewables["DE"])

def costs(capacities, share_renewables):
    """ 
    This is our objective function (total costs).
    """
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical = {key: renewables[key] * (emp.gens[key].sum().sum() / renewables[key].sum()) * share_renewables[key] for key in renewables}
    hypothetical = {key: hypothetical[key].resample('1h').mean() for key in hypothetical}
    # print(hypothetical["DE"])

    # Initialize graph
    G = nx.DiGraph()

    # Set line capacities
    core_country = "DE"
    for key, value in capacities.items(): # should not be DE
        G.add_edge(core_country, key, capacity=value)

    for i, _ in enumerate(hypothetical["DE"]):
        production_per_hour = {key: hypothetical[key].iloc[i] for key in hypothetical}
        consumption_per_hour = {key: loads[key].iloc[i] for key in loads}

        # Set power generation and consumption
        G = auto_start_end.start_end_node(G, production_per_hour, consumption_per_hour)

        flow_value, flow_dict = nx.maximum_flow(G, "Start", "Ziel", flow_func=shortest_augmenting_path)
        print(flow_value)
        print(flow_dict)

costs(
    {"BE" : 1000, "CH" : 1000, "CZ" : 1000, "DE" : 1000, "DK" : 1000, "FR" : 1000, "LU" : 1000, "NL" : 1000, "PL" : 1000},
    {"BE" : 1.0, "CH" : 1.0, "CZ" : 1.0, "DE" : 1.0, "DK" : 1.0, "FR" : 1.0, "LU" : 1.0, "NL" : 1.0, "PL" : 1.0}
)
# Frankreich: Atom gleich lassen