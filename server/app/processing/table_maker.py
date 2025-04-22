# app/processing/table_maker.py - Functions for preparing state table elements and equations

from typing import List, Tuple, Any, Dict
import math
from sympy import symbols, And, Or, Not, false, true, SOPform



def prepare_table_elements(filtered_nodes: List[dict]) -> Tuple[List[Any], List[str], List[str], dict]:
    """
    Extracts lists of states, inputs (decision conditions), and outputs
    (state/event data) from the list of filtered nodes.
    (Code from previous step - included for completeness)
    """
    print("--- Entering table_maker.py: prepare_table_elements ---")
    states = []
    inputs = []
    outputs = [] # Outputs are identified by their data content (names)

    if not filtered_nodes:
        print("TableMaker Warning: Received empty list of nodes.")
        return states, inputs, outputs

    unique_inputs = set()
    state_outputs = {}
    event_outputs = set()
    states = []

    for node in filtered_nodes:
        node_type = node.get('type')
        node_id = node.get('id')
        node_data = node.get('node_data', '') # Default to empty string

        if node_type == 'state':
            if node_id is not None:
                states.append(node_id)
                # Assumption: non-empty node_data in 'state' nodes represents Moore outputs
                if node_data:
                    node_data = node_data.splitlines()
                    state_outputs[node_id] = []
                    for i in node_data:
                        state_outputs[node_id].append(i)
            else:
                 print(f"TableMaker Warning: State node found with missing ID: {node}")

        elif node_type == 'decision':
            # Add the decision condition text as an input variable name
            if node_data:
                unique_inputs.add(node_data)

        elif node_type == 'event': # Handling for a potential 'event' type for Mealy outputs
             # If you have specific output boxes (e.g., type 'event' or 'output_box')
             # add their data to the outputs list.
             if node_data:
                  event_outputs.add(node_data)

        # Add other node type handling here if necessary

    # Convert sets to sorted lists for consistent order
    inputs_list = sorted(list(unique_inputs))
    event_outputs = sorted(list(event_outputs))
    states_list = sorted(list(states))

    print(f"TableMaker: Found {len(states_list)} states, {len(inputs_list)} unique inputs, {len(state_outputs) + len(event_outputs)} unique outputs.")
    print(f"--- Exiting table_maker.py: prepare_table_elements ---")
    return states_list, inputs_list, event_outputs, state_outputs


def assign_state_codes(states_list: List[Any]) -> Dict[Any, str]:
    """
    Assigns binary codes to each unique state ID.

    Args:
        states_list: A list of unique state IDs.

    Returns:
        A dictionary mapping each state ID to its binary code string.
        Returns an empty dictionary if the input list is empty.
    """
    print("--- Entering table_maker.py: assign_state_codes ---")
    state_codes = {}
    num_states = len(states_list)
    if num_states == 0:
        print("AssignCodes Warning: No states provided.")
        return state_codes

    # Determine the number of bits needed for state encoding
    num_bits = math.ceil(math.log2(num_states)) if num_states > 1 else 1

    # Assign binary codes sequentially (can be improved with state assignment algorithms later)
    for i, state_id in enumerate(states_list):
        # Format the binary code with leading zeros to match num_bits
        binary_code = format(i, f'0{num_bits}b')
        state_codes[state_id] = binary_code
        print(f"AssignCodes: State '{state_id}' -> Code '{binary_code}'")

    print(f"--- Exiting table_maker.py: assign_state_codes ({num_bits} bits) ---")
    return state_codes


def generate_boolean_equations(
    all_paths_formatted_details: List[List[List[Any]]],
    state_codes: Dict[Any, str],
    input_vars_list: List[str],
    event_outputs_list: List[str], # New parameter
    state_outputs_dict: Dict[Any, List[str]] # New parameter
) -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
    """
    Generates symbolic Boolean equations for next-state logic and outputs
    based on the processed FSM paths using SymPy. Handles separate logic
    for state-associated (Moore) and event-associated (Mealy) outputs.

    Args:
        all_paths_formatted_details: List of paths, where each path is a list
                                     of nodes formatted as [id, node_data, type, indicator].
        state_codes: Dictionary mapping state IDs to binary code strings.
        input_vars_list: List of input variable names (strings).
        event_outputs_list: List of output names associated with events (Mealy).
        state_outputs_dict: Dictionary mapping state IDs to output names (Moore).

    Returns:
        A tuple containing two dictionaries:
        1. next_state_eqns: Maps next-state variables (SymPy symbols like Y0_next)
                            to their SOP Boolean expressions (SymPy expressions).
        2. output_eqns: Maps output variables (SymPy symbols) to their SOP
                        Boolean expressions (SymPy expressions).
        Returns empty dictionaries if inputs are invalid or SymPy is unavailable.
    """
    print("--- Entering table_maker.py: generate_boolean_equations ---")
    next_state_eqns = {}
    output_eqns = {}

    if not all_paths_formatted_details or not state_codes:
        print("GenerateEquations Warning: No paths or state codes provided.")
        return next_state_eqns, output_eqns

    num_states = len(state_codes)
    num_bits = len(next(iter(state_codes.values()))) if num_states > 0 else 0
    if num_bits == 0:
        print("GenerateEquations Warning: State codes are invalid (0 bits).")
        return next_state_eqns, output_eqns

    # --- 1. Define SymPy Symbols ---
    # State variables (present state)
    Y = symbols(f'Y:{num_bits}') # Creates Y0, Y1, ...
    # Next state variables
    Y_next = symbols(f'Y:{num_bits}') # Creates Y_next0, Y_next1, ...
    # Input variables
    inputs_sym = {name: symbols(name) for name in input_vars_list}
    # Output variables (combine names from both event and state outputs)
    nested_list = state_outputs_dict.values()
    flat_list = [item for sublist in nested_list for item in sublist]
    all_output_names = set(event_outputs_list) | set(flat_list)
    outputs_sym = {name: symbols(name) for name in all_output_names}

    print(f"GenerateEquations: Defined symbols - State: {Y}, NextState: {Y_next}, Inputs: {list(inputs_sym.keys())}, Outputs: {list(outputs_sym.keys())}")

    # Initialize equations with 'false'
    for i in range(num_bits):
        next_state_eqns[Y_next[i]] = false
    for out_name in all_output_names:
        output_eqns[outputs_sym[out_name]] = false

    # --- 2. Process Each Path for Next State and Event (Mealy) Outputs ---
    for path in all_paths_formatted_details:
        if not path or path[0] is None: # Check if path is empty or starts with a missing node
             print(f"GenerateEquations Warning: Skipping invalid path: {path}")
             continue

        start_node_details = path[0]
        start_state_id = start_node_details[0]
        start_state_code = state_codes.get(start_state_id)

        if start_state_code is None:
            print(f"GenerateEquations Warning: State code not found for start state '{start_state_id}' in path. Skipping path.")
            continue

        # --- 3. Build RHS Product Term (Path Condition) ---
        # Start with the present state minterm
        present_state_term = true
        for i, bit in enumerate(start_state_code):
            term = Y[i] if bit == '1' else Not(Y[i])
            present_state_term = And(present_state_term, term)

        path_condition = present_state_term
        # Add input conditions from decisions along the path
        for i in range(1, len(path)): # Start from the second node
            current_node_details = path[i]
            prev_node_details = path[i-1]

            if current_node_details is None or prev_node_details is None:
                 print(f"GenerateEquations Warning: Path contains missing node details. Condition might be incomplete for path starting {start_state_id}.")
                 continue # Skip this step if data is missing

            indicator = current_node_details[3]
            if prev_node_details[2] == 'decision': # Check type of previous node
                decision_var_name = prev_node_details[1] # node_data holds the variable name
                decision_sym = inputs_sym.get(decision_var_name)
                if decision_sym is None:
                     print(f"GenerateEquations Warning: Input symbol not found for decision condition '{decision_var_name}'. Skipping condition.")
                     continue
                if indicator is True: input_term = decision_sym
                elif indicator is False: input_term = Not(decision_sym)
                else:
                    print(f"GenerateEquations Warning: Ambiguous path from decision '{decision_var_name}'. Indicator is {indicator}. Skipping condition.")
                    continue
                path_condition = And(path_condition, input_term)


        # --- 4. Assign RHS term to LHS (Next State and Event Outputs) ---
        end_node_details = path[-1]
        if end_node_details is None or end_node_details[2] != 'state':
            print(f"GenerateEquations Warning: Path does not end in a valid state node. Skipping assignment for path starting {start_state_id}.")
            continue # Path must end in a state

        end_state_id = end_node_details[0]
        end_state_code = state_codes.get(end_state_id)
        if end_state_code is None:
            print(f"GenerateEquations Warning: State code not found for end state '{end_state_id}'. Skipping assignment.")
            continue

        # Assign to Next State equations
        for i, bit in enumerate(end_state_code):
            if bit == '1':
                next_state_eqns[Y_next[i]] = Or(next_state_eqns[Y_next[i]], path_condition)

        # Assign to Event (Mealy) Output equations
        # Iterate through nodes in the path to find event outputs triggered by this path condition
        for i in range(len(path)):
             node_details = path[i]
             if node_details is None: continue
             node_data = node_details[1] # Output name is in node_data for event nodes
             node_type = node_details[2]

             # Check if this node represents an event output
             if node_type == 'event' and node_data in event_outputs_list:
                  if node_data in outputs_sym: # Check if symbol exists
                      output_sym = outputs_sym[node_data]
                      output_eqns[output_sym] = Or(output_eqns[output_sym], path_condition)
                  else:
                      print(f"GenerateEquations Warning: Output symbol not found for event output '{node_data}'.")


    # --- 5. Build State (Moore) Output Equations ---
    print("GenerateEquations: Building Moore output equations...")
    for state_id, output_list in state_outputs_dict.items():
        for output_name in output_list:
            if output_name in outputs_sym: # Check if output name is valid
                output_sym = outputs_sym[output_name]
                state_code = state_codes.get(state_id)
                if state_code:
                    # Build the state minterm for this state
                    state_minterm = true
                    for i, bit in enumerate(state_code):
                        term = Y[i] if bit == '1' else Not(Y[i])
                        state_minterm = And(state_minterm, term)
                    # OR this state's minterm into the output equation
                    output_eqns[output_sym] = Or(output_eqns[output_sym], state_minterm)
                else:
                    print(f"GenerateEquations Warning: State code not found for state '{state_id}' while building Moore output '{output_name}'.")
            else:
                print(f"GenerateEquations Warning: Output symbol not found for state output '{output_name}'.")




    print(f"--- Exiting table_maker.py: generate_boolean_equations ---")
    return next_state_eqns, output_eqns

