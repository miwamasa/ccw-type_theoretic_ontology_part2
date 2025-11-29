CFP synthesis prototype
-----------------------
Files:
- catalog.yaml : DSL catalog of types and functions
- synth_lib.py : library implementing Catalog and backward search
- run_prototype.py : simple runner that prints synthesis results for Product -> CO2

To run locally:
- Python 3.9+ required
- pip install pyyaml
- python run_prototype.py

Notes:
- This is a minimal prototype for demonstration: it does not execute SPARQL/REST/formula implementations.
- 'impl' entries are metadata only; to make this executable you must implement the execution layer:
  - SPARQL: call triplestore and return values
  - REST: call REST endpoints
  - formula: evaluate with given parameters (e.g. emission_factor, efficiency)
- The search here is backward Dijkstra-like (no heuristic). For large catalogs use A*/bidirectional search and pruning heuristics.
