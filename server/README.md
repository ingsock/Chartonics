# FSM Designer - Python Backend

This directory contains the Python backend for the FSM/ASM chart designer application.

## Functionality

- Receives FSM/ASM chart data (JSON) via a POST request.
- Parses the chart data.
- Reduces the chart to a state table.
- Uses SymPy for analysis/minimization (if applicable).
- Generates corresponding VHDL code.
- Returns the VHDL code (or status/errors) in the HTTP response.

## Setup

1.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

(Instructions to be added - e.g., using uvicorn)
```bash
# Example: uvicorn main:app --reload
```

## Project Structure

(Brief explanation of the directories)
