# main.py - Basic Flask server to receive Drawflow JSON data with CORS and file saving

# Import necessary modules
# Flask: The main class for creating the web application instance.
# request: An object that holds all incoming request data.
# jsonify: A function to convert Python dictionaries into JSON responses.
# CORS: Extension to handle Cross-Origin Resource Sharing headers.
from flask import Flask, request, jsonify
from flask_cors import CORS
import json # Import json module for loading/dumping JSON data
import app.processing.parser as parser # Import the parser module for processing Drawflow data
import app.processing.path_finder as path_finder # Import the path_finder module for finding paths in the Drawflow data
import app.processing.table_maker as table_maker # Import the table_maker module for preparing state table elements
import app.processing.state_reducer as state_reducer # Import the state_reducer module for simplifying equations
import app.processing.vhdl_generator as vhdl_generator # Import the vhdl_generator module for generating VHDL code
import pyperclip 

output_file_path = "output.vhd" # Initialize file handler to None

# Create an instance of the Flask class.
app = Flask(__name__)

# Enable CORS for all routes on this app instance.
# This is crucial for allowing requests from your frontend JavaScript
# running on a different origin (e.g., file:// or another localhost port).
CORS(app)

# Define a route for the API endpoint '/api/save-drawflow'
# methods=['POST']: This specifies that this route should only respond to HTTP POST requests.
@app.route('/api/save-drawflow', methods=['POST'])
def save_drawflow_data():
    """
    Handles POST requests to /api/save-drawflow.
    Expects JSON data, prints it nicely, saves it to a file,
    and returns a success response.
    Includes CORS support.
    """
    print("Received request at /api/save-drawflow") # Log that the endpoint was hit

    # Check if the request content type is JSON
    if not request.is_json:
        print("Error: Request content type is not JSON")
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400 # 400 Bad Request

    try:
        # Parse the JSON data from the incoming request into a Python dictionary/list
        drawflow_data = request.get_json()

        if drawflow_data is None:
             # This case might be less likely now with request.is_json check, but good practice
            print("Error: No JSON data received despite correct Content-Type.")
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        # --- Print the parsed data ---
        print("\n--- Received & Parsed Drawflow Data ---")
        # Use json.dumps() to convert the Python object back into a
        # nicely formatted JSON string for printing to the console.
        # indent=2 makes it human-readable.
        filtered = parser.parse_drawflow_data(drawflow_data)
         # Call the parser function to filter nodes
        link_path = path_finder.find_link_paths(filtered)
        paths = parser.get_formatted_details_for_all_paths(link_path, filtered)
        print(table_maker.prepare_table_elements(filtered))
        table = table_maker.prepare_table_elements(filtered)
        state_list, input_list, event_outputs, state_outputs = table
        state_codes = table_maker.assign_state_codes(state_list)

        equation = table_maker.generate_boolean_equations(paths, state_codes, input_list, event_outputs, state_outputs)

        simplified_state_equations = state_reducer.simplify_equations(equation[0])
        simplified_output_equations = state_reducer.simplify_equations(equation[1])
 
        nested_list = state_outputs.values()
        flat_list = [elem for sublist in nested_list for elem in sublist]
        total_output = flat_list + event_outputs
        vhdl_code = vhdl_generator.generate_vhdl("test", input_list, total_output, state_codes, simplified_state_equations, simplified_output_equations)
        with open(output_file_path, 'w') as f:
            f.write(vhdl_code)
        pyperclip.copy(vhdl_code) # Copy the generated VHDL code to the clipboard
        print("VHDL code copied to clipboard")
        print("WEEEEEEEE WOOOOOOOOOOO WAAAAAAAAAAAA WE ARE DONE") 


        # Print the filtered data in a readable format
        print("---------------------------------------\n")
        # --- End of printing ---
        # --- Save the data to a file ---
        try:
            # Use a 'with' statement for safer file handling (automatically closes file)
            with open('drawflow_export.json', 'w') as f:
                # Dump the Python dictionary directly to the file as JSON
                json.dump(drawflow_data, f, indent=2)
            print("Data successfully saved to drawflow_export.json")
        except Exception as e:
            # Catch potential file I/O errors
            print(f"Error saving data to file: {e}")
            # Decide if this should be a fatal error for the request or just logged
            # For now, we'll still return success to the client if printing worked,
            # but log the file save error. If saving is critical, return 500 here.
            # return jsonify({"status": "error", "message": f"Failed to save data: {e}"}), 500

        # --- End of saving ---

        # Send back a success response to the frontend
        response_data = {"status": "success", "message": "Data received and processed successfully!"}
        return jsonify(response_data), 200 # 200 OK status code

    except Exception as e:
        # Catch any other unexpected errors during JSON parsing or processing
        print(f"Error processing request: {e}")
        # Return a 500 Internal Server Error response
        return jsonify({"status": "error", "message": f"An internal server error occurred: {e}"}), 500

# This block checks if the script is being run directly
if __name__ == '__main__':
    # Run the Flask development server.
    # host='localhost': Listens only on the local machine interface.
    # port=5000: Sets the port number.
    # debug=True: Enables auto-reloading and detailed error pages.
    #             IMPORTANT: Do NOT use debug=True in production!
    print("Starting Flask server with CORS enabled on http://localhost:5000")
    app.run(host='localhost', port=5000, debug=True)

