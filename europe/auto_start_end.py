def start_end_node(graph, node_production, node_consumption):
    graph_new = graph.copy()
    for node in graph.nodes():
        if node != "Start" and node != "Ziel":
            graph_new.add_edge("Start", node, capacity=node_production[node])  # Verbinde den Startknoten mit jedem anderen Knoten
            graph_new.add_edge(node, "Ziel", capacity=node_consumption[node])
    return graph_new
