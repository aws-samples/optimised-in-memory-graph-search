# Graph Algorithms using In-Memory Python Hashmap as Repo

## Disclaimer

This repository of source code is a reference implementation not intended to be deployed for Production usage. Additional functional, load and security testing is required.

## About

This repository is a reference implementation of efficiently storing and querying graph data with a Python Flask API and an In-Memory hashmap.
This project is containerised so both `docker-compose` and `docker` commands would work. 

Commercially available graph databases are not a good fit to evaluate incremental, multi-step, conditional graph traversal problems either due to performance issues or significant licensing fees required.

The source code indexes relationship data with an In-Memory hashmap and implements the following 2 algorithms

1. Given a start node, retrieve the Graph of connected nodes with `n` degrees. 
2. Given a start and destination node, retrive all paths with `n` degrees of separation

The implementation for radial graph generation is mainly based on BFS, while path search from radial data is implemented with DFS algorithm. The relationship type of graph edges are also cached in the resulting radial graph.

The pre-processing is currently being triggered at the initiation of the Flask API web app. 

## Getting started locally

Utilise local resources to run the graph search application.

1. Clone the repo
2. Setup a virtualenv environment
3. Install dependencies from requirements.txt
4. Modify the launch parameters in flask.py main method
5. Launch flask.py to start loading CSV data and once ready, use the API for traversal and benchmark testing

## Getting started locally with Docker (docker-compose)

Ensure that you have Docker installed on your local machine.

1. Clone the repo
2. `docker-compose build`
3. `docker-compose up` to start the docker container. Use `-d` flag to detach from console, though this will also hide the memory profiles.

## API Usage Example

### Radial search
Example: `http://localhost:5001/radial?node=cfcd208495d565ef66e7dff9f98764da&degree=3&mode=showdata`
- Resource identifier: /radial/<start_node_id>/<int:degree>/<mode: 'benchmark' or 'showdata'>

### Path search
Example: `http://localhost:5001/paths?start=cfcd208495d565ef66e7dff9f98764da&end=000871c1fc726f0b52dc86a4eeb027de&dist=4`
- Resource identifier: /paths/<start_id>|<end_id>/<int:distance>

## Cache Compression Mapping with Pickle

When the constant ```LOAD_COMPRESSION_MAPS``` in ```os_graph.py``` is set to ```True```, the engine writes to disk a copy of the internal compression mapping between the data set node ids and the compressed internal ids. This allows the Flask API to accept the original node ids in the data set, and query with compressed ids internally at runtime.

To utilise this mapping cache at container up time to reduce the time taken for this process, first launch the engine direectly from ```flask_app.py``` to generate the pickle files. In the subsequent ```docker-compose build``` commands, the existing pickle files in the directory will be included and packaged into the container.

## About the Sample Data

The sample data included in this repository is a randomly generated Erdo Renyi graph with [NetworkX](https://networkx.org/) and [Pandas](https://pandas.pydata.org/) library. The graph contains 10,000 nodes with approximately 100,000 edges. The node names are hashed to reflect real world GUID length and complexity.
```
import networkx as nx

er = nx.erdos_renyi_graph(10000, 0.002)
```

## Key Contributors

### Derick Chen
[LinkedIn](linkedin.com/in/derick-chen) | [Github](https://github.com/buildwithdc)
- Played an instrumental role in developing the solution's traversal algorithms and API interface.
- Designed and created the file based caching system to improve container setup and initiation time. 
- Benchmarked load and speed benchmarking against commercially available Graph database solutions.
- Spearheaded the open source process.

### Raja SP
[LinkedIn](linkedin.com/in/spraja) | [Github](https://github.com/spraja08)
- Spearheaded the software and architectural design, evaluating multiple technologies for the best approach. 
- Designed the hashmap structure and optimised the compression algorithm to improve the scalability and speed of this graph search solution.
