def start_end_node(graph, node_production, node_consumption):
    graph_new = graph.copy()
    i = 0
    for node in graph.nodes():
        if node != "Start" and node != "Ziel":
            graph_new.add_edge("Start", node, capacity=node_production[i])  # Verbinde den Startknoten mit jedem anderen Knoten
            graph_new.add_edge(node, "Ziel", capacity=node_consumption[i])
            i += 1
    return graph_new
