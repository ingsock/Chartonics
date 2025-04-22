# app/processing/parser.py - Functions for parsing Drawflow JSON data and retrieving node details

import json # Used for potentially dumping intermediate results or handling JSON strings if needed

def parse_drawflow_data(drawflow_data: dict) -> list:
    """
    Parses the raw Drawflow data dictionary to extract essential node information,
    including the node's specific data content.

    Args:
        drawflow_data: The full dictionary parsed from the incoming JSON request.

    Returns:
        A list of dictionaries, where each dictionary represents a node
        and contains its 'id', 'type' (from 'name'), 'inputs', 'outputs',
        and 'node_data' (content from the node's data field).
        Returns an empty list if the expected data structure is not found or is invalid.
    """
    print("--- Entering parser.py: parse_drawflow_data ---") # Log entry into the function
    filtered_nodes = []

    # Safely navigate the dictionary structure using .get() to avoid KeyErrors
    # Assumes the main data is under drawflow -> Home -> data
    nodes_data = drawflow_data.get('drawflow', {}).get('Home', {}).get('data', {})

    if not isinstance(nodes_data, dict):
         print("Parser Error: Expected 'data' field within drawflow['Home'] to be a dictionary.")
         return [] # Return empty list if structure is invalid

    # Iterate through each node definition in the 'data' dictionary
    for node_id, node_obj in nodes_data.items(): # Iterate using items() to access both key (node_id) and value (node_obj)
        # Check if the node_obj is a dictionary and has the required keys
        if isinstance(node_obj, dict) and all(k in node_obj for k in ['id', 'name', 'inputs', 'outputs', 'data']): # Added 'data' check
            # Basic validation: Check if the object's id matches its key in the dictionary
            if str(node_obj.get('id')) != str(node_id):
                 print(f"Warning: Node ID mismatch for key '{node_id}'. Object ID: {node_obj.get('id')}. Skipping.")
                 continue # Skip this node if IDs don't match

            # --- Extract node_data content ---
            # Access the nested 'data' field where user input is often stored
            node_specific_data_content = node_obj.get('data', {}).get('data', '') # Default to empty string if not found
            # ---------------------------------

            filtered_node = {
                'id': node_obj.get('id'), # Store original ID type (usually int)
                'type': node_obj.get('name'), # Using 'name' as the node type ('state', 'decision')
                'inputs': node_obj.get('inputs', {}), # Get inputs, default to empty dict if missing
                'outputs': node_obj.get('outputs', {}), # Get outputs, default to empty dict if missing
                'node_data': node_specific_data_content # Add the extracted node data content
            }
            filtered_nodes.append(filtered_node)
        else:
            print(f"Warning: Skipping node object with key '{node_id}' due to missing keys or incorrect format: {node_obj}")

    print(f"--- Exiting parser.py: Parsed {len(filtered_nodes)} nodes ---") # Log exit and count
    return filtered_nodes


# --- Renamed and modified function ---
def get_formatted_details_for_all_paths(all_paths_ids: list, filtered_nodes: list) -> list:
    """
    Takes a list of paths (each path being a list of node IDs) and
    returns a corresponding list of paths where IDs are replaced with
    formatted node details: [id, node_data, type, indicator].
    The indicator is True if input_1 comes from previous node's output_1,
    False if it comes from previous node's output_2, None otherwise or for the first node.

    Args:
        all_paths_ids: A list of lists, where each inner list contains node IDs
                       representing a path (output from find_link_paths).
        filtered_nodes: The list of filtered node dictionaries (output from
                        parse_drawflow_data, must include 'node_data').

    Returns:
        A list of lists of lists. The outer list corresponds to the input paths.
        Each inner list contains the formatted details [id, data, type, indicator]
        for nodes in that path. Returns an empty list if inputs are invalid.
    """
    print(f"--- Entering parser.py: get_formatted_details_for_all_paths for {len(all_paths_ids)} paths ---")
    all_paths_formatted_details = [] # Outer list for all paths

    if not all_paths_ids or not filtered_nodes:
        print("Formatter Warning: Received empty all_paths_ids or filtered_nodes.")
        return all_paths_formatted_details

    # --- 1. Build a map for easy node lookup by ID (once for all paths) ---
    # Ensure keys are strings, matching the IDs in path_ids from path_finder
    nodes_map = {str(node.get('id')): node for node in filtered_nodes if node.get('id') is not None}

    if not nodes_map:
         print("Formatter Error: Failed to build node map from filtered_nodes.")
         return all_paths_formatted_details

    # --- 2. Iterate through each path of IDs in the input list ---
    for path_index, single_path_ids in enumerate(all_paths_ids):
        formatted_single_path = [] # Inner list for the current path's details
        if not isinstance(single_path_ids, list):
             print(f"Formatter Warning: Path at index {path_index} is not a list: {single_path_ids}. Skipping.")
             all_paths_formatted_details.append(None) # Add placeholder for malformed path input
             continue

        # --- 3. Iterate through each ID in the current single path ---
        for node_index, node_id in enumerate(single_path_ids):
            # Ensure node_id is treated as a string for lookup
            current_node_data_dict = nodes_map.get(str(node_id))

            if current_node_data_dict:
                # --- 4. Extract basic details ---
                node_id_val = current_node_data_dict.get('id')
                node_data_content = current_node_data_dict.get('node_data', '') # Get the added node data
                node_type = current_node_data_dict.get('type')

                # --- 5. Determine the indicator ---
                indicator = None # Default for first node or if connection unclear
                if node_index > 0: # Cannot determine indicator for the first node (no previous node)
                    previous_node_id = single_path_ids[node_index - 1]
                    # Find the connection to input_1 of the current node that comes from the previous node
                    current_inputs = current_node_data_dict.get('inputs', {})
                    input_1_connections = current_inputs.get('input_1', {}).get('connections', [])

                    for conn in input_1_connections:
                        # Check if the connection's source node is the previous node in the path
                        if str(conn.get('node')) == str(previous_node_id):
                            originating_port = conn.get('input')
                            if originating_port == 'output_1':
                                indicator = True
                                break # Found the relevant connection
                            elif originating_port == 'output_2':
                                indicator = False
                                break # Found the relevant connection
                            else:
                                # Connection from previous node, but unexpected port name
                                print(f"Formatter Warning: Node {node_id_val} input_1 connected to unexpected port '{originating_port}' of previous node {previous_node_id}.")
                                # Keep indicator as None
                                break
                    # If loop finishes without break, indicator remains None (connection from prev node to input_1 not found)
                    if indicator is None and len(input_1_connections) > 0:
                         # This case might indicate an issue if we expect a connection from the previous node
                         pass # Silently keep indicator=None, or add specific warning if needed

                # --- 6. Create the formatted list for this node ---
                formatted_node_detail = [
                    node_id_val,
                    node_data_content,
                    node_type,
                    indicator # Add the calculated indicator
                ]
                formatted_single_path.append(formatted_node_detail)
            else:
                # Handle case where an ID in the path doesn't exist in the map
                print(f"Formatter Warning: Node ID '{node_id}' from path {single_path_ids} not found in nodes map.")
                formatted_single_path.append(None) # Append None as a placeholder for the missing node

        # Append the list of formatted details for the current path to the overall list
        all_paths_formatted_details.append(formatted_single_path)

    print(f"--- Exiting parser.py: Formatted details for {len(all_paths_formatted_details)} paths ---")
    return all_paths_formatted_details

