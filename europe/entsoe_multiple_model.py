import entsoe_multiple_preprocess as emp
import networkx as nx

for key in emp.loads_from_json:
    print(key)
    print(emp.loads_from_json[key])

for key in emp.gens_from_json:
    print(key)
    print(emp.gens_from_json[key])

G = nx.DiGraph()

core_country = "DE"
for key in emp.loads_from_json:
    if key != core_country:
        G.add_edge(core_country, key, capacity=0)