# app/processing/vhdl_generator.py - Generates VHDL code from FSM equations

from typing import List, Dict, Any, Tuple

# Import SymPy to check types and access properties
try:
    import sympy
    from sympy import Symbol, And, Or, Not, true, false
except ImportError:
    print("\n*** SymPy library not found. Please install it: pip install sympy ***\n")
    # Define dummy classes/values if sympy is not available
    class Symbol: pass
    class And: pass
    class Or: pass
    class Not: pass
    true = "sympy_true"
    false = "sympy_false"
    sympy_available = False
else:
    sympy_available = True

# Helper function to map SymPy state variables (Y0, Y1...) to VHDL signal bits
def _get_state_bit_vhdl(symbol: Symbol, state_vars: Tuple[Symbol], signal_name: str) -> str:
    """Maps a state variable symbol (Y0) to its VHDL signal slice (current_state(0))."""
    try:
        index = state_vars.index(symbol)
        return f"{signal_name}({index})"
    except ValueError:
        # Should not happen if symbol is confirmed to be a state variable
        return f"'{symbol.name}_ERROR'"

def sympy_expr_to_vhdl(expr: Any, state_vars: Tuple[Symbol], state_signal_name: str = "current_state") -> str:
    """
    Recursively converts a SymPy Boolean expression into a VHDL string.

    Args:
        expr: The SymPy expression (e.g., And(x, Not(Y0))).
        state_vars: A tuple of the SymPy symbols representing state variables (Y0, Y1,...).
        state_signal_name: The base name of the VHDL signal holding the current state.

    Returns:
        A string containing the VHDL equivalent expression.
    """
    if not sympy_available:
        return f"'{str(expr)}_SYMPY_UNAVAILABLE'"

    # Base cases
    if expr == true:
        return "'1'"
    if expr == false:
        return "'0'"

    # Recursive cases
    if isinstance(expr, Not):
        # VHDL 'not' has high precedence, parentheses might be needed depending on context,
        # but often okay if the operand is simple or already parenthesized.
        # Adding parentheses defensively.
        operand_vhdl = sympy_expr_to_vhdl(expr.args[0], state_vars, state_signal_name)
        return f"(not {operand_vhdl})"
    elif isinstance(expr, And):
        # Join arguments with ' and ', ensuring recursive conversion and parentheses
        args_vhdl = [f"({sympy_expr_to_vhdl(arg, state_vars, state_signal_name)})" for arg in expr.args]
        return " and ".join(args_vhdl)
    elif isinstance(expr, Or):
        # Join arguments with ' or ', ensuring recursive conversion and parentheses
        args_vhdl = [f"({sympy_expr_to_vhdl(arg, state_vars, state_signal_name)})" for arg in expr.args]
        return " or ".join(args_vhdl)
    elif isinstance(expr, Symbol):
        # Check if it's a state variable
        if expr in state_vars:
            return _get_state_bit_vhdl(expr, state_vars, state_signal_name)
        else:
            # Assume it's an input or output variable name
            return str(expr.name)
    else:
        # Handle unexpected types
        print(f"VHDLGen Warning: Unexpected expression type '{type(expr)}': {expr}")
        return f"'UNEXPECTED_EXPR_{type(expr).__name__}'"


def generate_vhdl(
    entity_name: str,
    inputs_list: List[str],
    outputs_list: List[str], # Combined list of all output names
    state_codes: Dict[Any, str],
    simplified_next_state_eqns: Dict[Any, Any],
    simplified_output_eqns: Dict[Any, Any]
) -> str:
    """
    Generates the complete VHDL code for the FSM.

    Args:
        entity_name: The desired name for the VHDL entity.
        inputs_list: List of input port names.
        outputs_list: List of output port names.
        state_codes: Dictionary mapping state IDs to binary codes.
        simplified_next_state_eqns: Dictionary mapping Y_next symbols to simplified SymPy expressions.
        simplified_output_eqns: Dictionary mapping output symbols to simplified SymPy expressions.

    Returns:
        A string containing the generated VHDL code. Returns error message if critical info missing.
    """
    print(f"--- Entering vhdl_generator.py: generate_vhdl (Entity: {entity_name}) ---")

    if not state_codes or not (simplified_next_state_eqns or simplified_output_eqns):
        print("VHDLGen Error: Missing state codes or equations.")
        return "-- VHDL Generation Error: Missing state codes or equations."
    if not sympy_available:
        print("VHDLGen Error: SymPy library is not available.")
        return "-- VHDL Generation Error: SymPy library is not available."
    outputs_list = list(set(outputs_list))
    num_states = len(state_codes)
    num_bits = len(next(iter(state_codes.values()))) if num_states > 0 else 0
    if num_bits == 0 and num_states > 0: # Allow 0 bits only if 0 states (edge case)
        print("VHDLGen Error: Invalid state codes (0 bits).")
        return "-- VHDL Generation Error: Invalid state codes (0 bits)."

    # Define state variable symbols (matching those used in equation generation)
    # These are needed for the sympy_expr_to_vhdl mapping
    Y = sympy.symbols(f'Y:{num_bits}') if num_bits > 0 else tuple()
    Y_next_syms = sympy.symbols(f'Y:{num_bits}') if num_bits > 0 else tuple()
    # Ensure Y and Y_next_syms are tuples even if num_bits is 1

    # Determine initial state (e.g., first state in list or all zeros)
    # Using all zeros as a common default reset state
    reset_state_code = '0' * num_bits if num_bits > 0 else ""

    # --- VHDL Template ---
    vhdl_code = f"""
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity {entity_name} is
    port (
        clk     : in  std_logic;
        reset   : in  std_logic;
"""
    # Input Ports
    if inputs_list:
        vhdl_code += "\n        -- Inputs\n"
        for input_name in inputs_list:
            vhdl_code += f"        {input_name.ljust(8)}: in  std_logic;\n"

    # Output Ports (remove trailing semicolon from last input if outputs exist)
    if outputs_list:
         if inputs_list: # Adjust semicolon if inputs were present
              vhdl_code = vhdl_code.rstrip().removesuffix(';') + ';\n'
         vhdl_code += "\n        -- Outputs\n"
         for i, output_name in enumerate(outputs_list):
              vhdl_code += f"        {output_name.ljust(8)}: out std_logic"
              if i < len(outputs_list) - 1:
                  vhdl_code += ";\n"
              else:
                  vhdl_code += "\n" # No semicolon on last port
    elif inputs_list: # No outputs, remove semicolon from last input
         vhdl_code = vhdl_code.rstrip().removesuffix(';') + '\n'


    vhdl_code += f"""\
    );
end entity {entity_name};

architecture Behavioral of {entity_name} is

    -- State register and next state logic signals
"""
    if num_bits > 0:
        vhdl_code += f"    signal current_state, next_state : std_logic_vector({num_bits - 1} downto 0);\n"
    else: # Handle case with no state bits (e.g., combinational only logic?)
         vhdl_code += "    -- No state bits defined.\n"

    # Optional: State type definition for readability (not strictly needed for this logic)
    # type state_type is (S0, S1, S2); -- Example
    # signal current_state_enum, next_state_enum : state_type;

    # Define output symbols map for lookup
    outputs_sym_map = {str(sym): sym for sym in sympy.symbols(','.join(outputs_list))} if outputs_list else {}

    vhdl_code += f"""
begin

    -- Combinational logic for next state and outputs
    process (current_state"""

    # Add inputs to sensitivity list
    if inputs_list:
        vhdl_code += ", " + ", ".join(inputs_list)
    vhdl_code += ")\n    begin\n"

    # Default assignments (optional, can prevent latches if logic is incomplete)
    # vhdl_code += f"        next_state <= current_state; -- Default assignment\n"
    # for output_name in outputs_list:
    #      vhdl_code += f"        {output_name} <= '0'; -- Default assignment\n"

    vhdl_code += "\n        -- Next State Logic\n"
    if num_bits > 0:
        for i in range(num_bits):
            next_state_var = Y_next_syms[i]
            if next_state_var in simplified_next_state_eqns:
                eqn_str = sympy_expr_to_vhdl(simplified_next_state_eqns[next_state_var], Y, "current_state")
                vhdl_code += f"        next_state({i}) <= {eqn_str};\n"
            else:
                # Handle case where equation might be missing (should ideally be present or false)
                vhdl_code += f"        next_state({i}) <= '0'; -- Default/missing equation for Y_next{i}\n"
    else:
         vhdl_code += "        -- No next state logic (0 state bits).\n"


    vhdl_code += "\n        -- Output Logic\n"
    if outputs_list:
        for output_name in outputs_list:
             output_sym = outputs_sym_map.get(output_name)
             if output_sym and output_sym in simplified_output_eqns:
                 eqn_str = sympy_expr_to_vhdl(simplified_output_eqns[output_sym], Y, "current_state")
                 vhdl_code += f"        {output_name} <= {eqn_str};\n"
             else:
                 # Handle case where equation might be missing (should ideally be present or false)
                  vhdl_code += f"        {output_name} <= '0'; -- Default/missing equation for {output_name}\n"
    else:
         vhdl_code += "        -- No output logic defined.\n"


    vhdl_code += f"""
    end process;

    -- State Register (Sequential logic)
    process (clk, reset)
    begin
        if reset = '1' then
"""
    if num_bits > 0:
        vhdl_code += f"            current_state <= \"{reset_state_code}\"; -- Reset state\n"
    else:
        vhdl_code += "            -- No state register to reset.\n"

    vhdl_code += f"""\
        elsif rising_edge(clk) then
"""
    if num_bits > 0:
        vhdl_code += "            current_state <= next_state;\n"
    else:
         vhdl_code += "            -- No state register to update.\n"

    vhdl_code += f"""\
        end if;
    end process;

end architecture Behavioral;
"""
    print(f"--- Exiting vhdl_generator.py: generate_vhdl ---")
    return vhdl_code