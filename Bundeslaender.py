import networkx as nx
import matplotlib.pyplot as plt

G = nx.DiGraph()

# G.add_nodes_from("n","nrw","be","bw","ba")
G.add_edge("SH", "N", capacity=10)
G.add_edge("SH", "HH", capacity=10)
G.add_edge("SH", "MV", capacity=1)
G.add_edge("N", "HB", capacity=7)
G.add_edge("N", "HH", capacity=7)
G.add_edge("N", "MV", capacity=1)
G.add_edge("N", "NRW", capacity=10)
G.add_edge("N", "HS", capacity=10)
G.add_edge("N", "T", capacity=10)
G.add_edge("N", "SA", capacity=10)
G.add_edge("N", "BR", capacity=1)
G.add_edge("MV", "N", capacity=1)
G.add_edge("MV", "BR", capacity=10)
G.add_edge("BR", "B", capacity=10)
G.add_edge("BR", "N", capacity=1)
G.add_edge("BR", "SA", capacity=10)
G.add_edge("BR", "S", capacity=10)
G.add_edge("SA", "T", capacity=10)
G.add_edge("SA", "S", capacity=1)
G.add_edge("T", "BY", capacity=10)
G.add_edge("T", "S", capacity=1)
G.add_edge("T", "HS", capacity=1)
G.add_edge("NRW", "HS", capacity=10)
G.add_edge("NRW", "RP", capacity=10)
G.add_edge("HS", "BY", capacity=10)
G.add_edge("HS", "T", capacity=1)
G.add_edge("HS", "BW", capacity=10)
G.add_edge("HS", "RP", capacity=1)
G.add_edge("RP", "SL", capacity=1)
G.add_edge("RP", "NRW", capacity=1)
G.add_edge("RP", "BW", capacity=10)
G.add_edge("RP", "HS", capacity=1)
G.add_edge("SL", "RP", capacity=10)
G.add_edge("BY", "BW", capacity=1)

from networkx.algorithms.flow import shortest_augmenting_path

flow_value, flow_dict = nx.maximum_flow(G, "N", "BW", flow_func=shortest_augmenting_path)
print(G.in_edges("ba"))  # => [('a', 'e'), ('d', 'e')]
print(flow_value)
print(flow_dict)

#node_sizes = [500, 700, 600, 800, 900]
elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["capacity"] > 5]
esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["capacity"] <= 5]

pos = nx.spring_layout(G, seed=7)  # positions for all nodes - seed for reproducibility

# nodes
nx.draw_networkx_nodes(G, pos, node_size=500)

# edges
nx.draw_networkx_edges(G, pos, edgelist=elarge, width=6)
nx.draw_networkx_edges(G, pos, edgelist=esmall, width=3, alpha=0.5, edge_color="b", style="dashed")

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

# Quelle Stromdifferenz Bundesland: https://www.iwd.de/artikel/die-kluft-zwischen-stromerzeugung-und-stromverbrauch-462633/
# Quelle Stromnetz: https://energiewinde.orsted.de/energiepolitik/stromnetz-ausbau-deutschland-fortschritt-proteste-gerichtsverfahren-karte
