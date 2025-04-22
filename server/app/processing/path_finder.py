# app/processing/path_finder.py - Finds paths between state nodes

import json # For potential debugging prints

def find_link_paths(filtered_nodes: list) -> list:
    """
    Finds all paths that start at a 'state' node, go through intermediate
    nodes (like 'decision', 'event'), and end at the next 'state' node.

    Args:
        filtered_nodes: A list of node dictionaries, each containing
                        'id', 'type', 'inputs', and 'outputs', as returned
                        by the parser.

    Returns:
        A list of lists, where each inner list represents a link path
        containing the sequence of node IDs from start state to end state.
        e.g., [[start_state_id, intermediate_id, ..., end_state_id], ...]
    """
    print("--- Entering path_finder.py: find_link_paths ---")
    link_paths = []
    if not filtered_nodes:
        print("PathFinder Warning: Received empty list of nodes.")
        return link_paths

    # --- 1. Build a map for easy node lookup by ID ---
    nodes_map = {}
    start_node_ids = []
    
    for node in filtered_nodes:
        node_id = node.get('id')
        if node_id is not None:
            nodes_map[str(node_id)] = node # Use string IDs consistent with connection data
            if node.get('type') == 'state':
                start_node_ids.append(str(node_id))
        else:
            print(f"PathFinder Warning: Node missing 'id': {node}")

    if not nodes_map:
         print("PathFinder Error: Failed to build node map.")
         return link_paths
    if not start_node_ids:
         print("PathFinder Warning: No 'state' nodes found to start paths from.")
         return link_paths

    print(f"PathFinder: Built map for {len(nodes_map)} nodes. Found {len(start_node_ids)} starting states.")

    # --- 2. Perform DFS from each starting 'state' node ---
    for start_id in start_node_ids:
        print(f"PathFinder: Starting DFS from state node '{start_id}'")
        # Initial path starts with the starting state ID
        # visited_in_path prevents cycles within a single path search
        _dfs_find_paths(start_id, [start_id], nodes_map, link_paths, set())

    print(f"--- Exiting path_finder.py: Found {len(link_paths)} link paths ---")
    return link_paths


def _dfs_find_paths(current_node_id: str, current_path: list, nodes_map: dict, link_paths: list, visited_in_path: set):
    """
    Recursive Depth-First Search helper function to find paths.

    Args:
        current_node_id: The ID of the node currently being visited (as string).
        current_path: The list of node IDs visited so far in this path.
        nodes_map: The dictionary mapping node IDs to node objects.
        link_paths: The list where complete paths are stored.
        visited_in_path: A set of node IDs visited in the current DFS traversal
                         to detect cycles within intermediate nodes.
    """
    current_node = nodes_map.get(current_node_id)
    if not current_node:
        print(f"PathFinder DFS Error: Node '{current_node_id}' not found in map.")
        return # Should not happen if map is built correctly

    # Add current node to the visited set for this specific path traversal
    visited_in_path.add(current_node_id)

    outputs = current_node.get('outputs', {})
    if not outputs:
        # Node has no outputs, path ends here (might be an unconnected node)
        # print(f"PathFinder DFS: Node '{current_node_id}' has no outputs. Path ends.")
        # Remove from visited set before returning (backtracking)
        visited_in_path.remove(current_node_id)
        return

    # Iterate through each output port of the current node (e.g., 'output_1', 'output_2')
    for output_port, port_data in outputs.items():
        connections = port_data.get('connections', [])
        # Iterate through each connection originating from this output port
        for connection in connections:
            target_node_id = connection.get('node') # Target node ID (string)
            # target_input_port = connection.get('input') # Target node's input port (unused here for now)

            if not target_node_id:
                # print(f"PathFinder DFS Warning: Connection from node '{current_node_id}' (port {output_port}) is missing target node ID.")
                continue

            target_node = nodes_map.get(target_node_id)
            if not target_node:
                print(f"PathFinder DFS Warning: Target node '{target_node_id}' (from node '{current_node_id}') not found in map. Skipping connection.")
                continue

            target_node_type = target_node.get('type')

            # --- Path Logic ---
            if target_node_type == 'state':
                # Path found! It ends at another state node.
                complete_path = current_path + [target_node_id]
                print(f"PathFinder DFS: Found path: {' -> '.join(complete_path)}")
                link_paths.append(complete_path)
                # Do not continue DFS further from this end state for this path search
            elif target_node_id in visited_in_path:
                # Cycle detected involving intermediate nodes (non-states)
                print(f"PathFinder DFS: Cycle detected involving intermediate node '{target_node_id}'. Path: {' -> '.join(current_path + [target_node_id])}. Stopping this branch.")
                # Stop traversing this branch to avoid infinite loops
            else:
                # Target is an intermediate node (decision, event, etc.) and not visited yet in this path. Continue DFS.
                _dfs_find_paths(target_node_id, current_path + [target_node_id], nodes_map, link_paths, visited_in_path.copy()) # Pass a copy of visited set

    # Backtrack: Remove current node from visited set after exploring all its outputs
    if current_node_id in visited_in_path:
         visited_in_path.remove(current_node_id)

