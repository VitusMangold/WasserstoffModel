import networkx as nx
import matplotlib.pyplot as plt
import random
import numpy as np
from networkx.algorithms.flow import shortest_augmenting_path
import auto_start_end


G = nx.DiGraph()


#Knoten
G.add_node("DE")
G.add_node("AU")
G.add_node("ES")
G.add_node("PO")
G.add_node("DM")


#Kanten
G.add_edge("DE", "ES", capacity=10)
G.add_edge("DE", "PO", capacity=10)
G.add_edge("ES", "DE", capacity=7)
G.add_edge("DM", "DE", capacity=10)
G.add_edge("DM", "PO", capacity=10)
G.add_edge("PO", "DE", capacity=10)
G.add_edge("AU", "DE", capacity=10)
G.add_edge("AU", "PO", capacity=10)
flow_DE_ES = np.zeros(24)
flow_ES_DE = np.zeros(24)
time = np.zeros(24)

print(G.nodes())

for i in range(0, 24):
    production_per_hour = random.choices(range(15), k=nx.number_of_nodes(G))
    consumption_per_hour = random.choices(range(15), k=nx.number_of_nodes(G))
    G = auto_start_end.start_end_node(G, production_per_hour, consumption_per_hour)
    flow_value, flow_dict = nx.maximum_flow(G, "Start", "Ziel", flow_func=shortest_augmenting_path)
    print(production_per_hour)
    print(consumption_per_hour)
    print(G.in_edges("ba"))  # => [('a', 'e'), ('d', 'e')]
    print("Flow value: ", flow_value)
    print(flow_dict)
    flow_DE_ES[i] = flow_dict["DE"]["ES"]
    flow_ES_DE[i] = flow_dict["ES"]["DE"]
    time[i] = i


#plot
plt.plot(time, flow_DE_ES, label = 'DE--ES')
plt.plot(time, flow_ES_DE, label = 'ES--DE')
plt.ylabel('Einheiten')
plt.legend(loc = 'upper right')
plt.xlabel('Zeit')
plt.title('Input')
plt.figure()

print(flow_DE_ES)
print(flow_ES_DE)


# Festlegen der Positionen der Knoten
pos = {"Start": (0.5, 2), "DE": (0.5, 0), "ES": (0, -1), "AU": (1, -1), "DM": (0.5, 1), "PO": (1, 0), "Ziel": (0.5, -2)}


# node_sizes = [500, 700, 600, 800, 900]
elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["capacity"] > 5]
esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["capacity"] <= 5]

# nodes
nx.draw_networkx_nodes(G, pos, node_size=500)

# edges
nx.draw_networkx_edges(G, pos, edgelist=elarge, width=4)
nx.draw_networkx_edges(G, pos, edgelist=esmall, width=2, alpha=0.5, edge_color="b", style="dashed")

# node labels
nx.draw_networkx_labels(G, pos, font_size=20, font_family="sans-serif")
# edge capacity labels
edge_labels = nx.get_edge_attributes(G, "capacity")
nx.draw_networkx_edge_labels(G, pos, edge_labels)

ax = plt.gca()
ax.margins(0.08)
plt.axis("off")
plt.tight_layout()
plt.show()

