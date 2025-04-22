# app/processing/state_reducer.py - Functions for simplifying Boolean equations

from typing import Dict, Any

# Import SymPy for symbolic boolean algebra
# Ensure sympy is installed: pip install sympy
try:
    import sympy
    # Import the correct simplification function
    from sympy.logic.boolalg import simplify_logic
except ImportError:
    print("\n*** SymPy library not found. Please install it: pip install sympy ***\n")
    # Define dummy function if sympy is not available
    simplify_logic = lambda expr, form=None, force=False: f"simplify_logic({expr}, form={form}, force={force})" # Dummy function
    sympy_available = False
else:
    sympy_available = True

def simplify_equations(equations_dict: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Simplifies a dictionary of SymPy Boolean expressions into SOP form
    using simplify_logic(form='dnf').

    Args:
        equations_dict: A dictionary where keys are variable symbols (like Y_next0 or output 'a')
                        and values are their corresponding raw SymPy Boolean expressions.

    Returns:
        A dictionary with the same keys but with simplified SymPy expressions
        in Sum-of-Products (SOP/DNF) form. If simplification fails for an
        expression, the original expression is returned for that key.
        Returns an empty dictionary if SymPy is unavailable.
    """
    print("--- Entering state_reducer.py: simplify_equations ---")
    simplified_equations = {}

    if not sympy_available:
        print("SimplifyEquations Error: SymPy library is not available. Cannot simplify.")
        return simplified_equations # Return empty if no sympy

    if not equations_dict:
        print("SimplifyEquations Warning: Received empty dictionary of equations.")
        return simplified_equations

    for variable, expression in equations_dict.items():
        print(f"Simplifying equation for: {variable}")
        try:
            # Use simplify_logic with form='dnf' to get SOP.
            # force=True removes variable limit, potentially slow but often needed.
            simplified_expr = simplify_logic(expression, form='dnf', force=True)
            simplified_equations[variable] = simplified_expr
            print(f"  Original: {expression}")
            print(f"  Simplified (SOP/DNF): {simplified_expr}")
        except Exception as e:
            # Catch potential errors during simplification
            print(f"SimplifyEquations Warning: Failed to simplify equation for {variable}. Error: {e}")
            print(f"  Using unsimplified expression: {expression}")
            simplified_equations[variable] = expression # Keep original if simplification fails

    print(f"--- Exiting state_reducer.py: simplify_equations ---")
    return simplified_equations