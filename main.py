import networkx as nx
import matplotlib.pyplot as plt

# Erstelle einen leeren, ungerichteten Graphen
G = nx.Graph()

# Füge die Städte als Knoten hinzu (A= Niedersachsen, B=NRW, C = Berlin, D = BW, E = BY)
nodes = {'A': 5, 'B': 2, 'C': 3, 'D': -1, 'E': -4}
for node, value in nodes.items():
    G.add_node(node, value=value)

# Füge die Verbindungen zwischen den Städten hinzu
connections = {
    'A': ['B', 'C'],
    'B': ['A', 'C', 'D', 'E'],
    'C': ['A', 'B', 'E'],
    'D': ['B'],
    'E': ['B', 'C']
}

for node, neighbors in connections.items():
    for neighbor in neighbors:
        G.add_edge(node, neighbor)

# Zeichne den Graphen
pos = nx.spring_layout(G)  # Bestimme die Position der Knoten
node_labels = {city: f"{node} ({value})" for city, value in nodes.items()}  # Beschrifte die Knoten mit Städtenamen und Werten

# Zeichne die Knoten und Kanten
nx.draw(G, pos, with_labels=True, labels=node_labels, node_size=1500, node_color='skyblue', font_size=12, font_weight='bold')
plt.title('Graph der Städte und Verbindungen')
plt.show()
