def start_end_node(graph):
    graph_new = graph.copy()
    for node in graph.nodes():
        if node != "Start" and node != "Ziel":
            # Verbinde den Startknoten mit jedem anderen Knoten
            graph_new.add_edge("Start", node, capacity= 0)
            graph_new.add_edge(node, "Ziel", capacity= 0)
    return graph_new, list(graph_new.nodes())


def start_end_node_capacity(graph, node_production, node_consumption, node_list):
    
    for node in node_list:
        if node != "Start" and node != "Ziel":
            # add the new capacity to the edge
            graph["Start"][node]["capacity"] = node_production[node]  
            graph[node]["Ziel"]["capacity"] = node_consumption[node]
    return graph


# Erstellen eines 2D-Arrays mit Listen in Listen
neighbors = [
    ["NL", "BE", "LU", "FR", "CH", "AT", "DK", "PL", "CZ"],
    ["BE", "DE", "DK"],
    ["LU", "NL", "DE", "FR"],
    ["FR", "BE", "DE"],
    ["ES", "IT", "CH", "DE", "LU", "BE"],
    ["FR"],
    ["FR", "AU", "CH"],
    ["AT", "DE", "IT", "FR"],
    ["DE", "CH", "IT", "CZ"],
    ["DE", "AT", "PL"],
    ["CZ", "DE"],
    ["DE", "NL"]
]

order_list_neighbors = ["DE", "NL", "BE", "LU", "FR", "ES", "IT", "CH", "AT", "CZ", "PL", "DK"]
