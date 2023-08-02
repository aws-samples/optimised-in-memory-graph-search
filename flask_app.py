# Copyright 2023 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

import logging
import sys

from flask import Flask, jsonify, request

from configure_logger import init_logger
from os_graph import Graph

app = Flask(__name__)
BENCHMARK_MODE = "benchmark"
LIVE_MODE = "showdata"
init_logger()


@app.route("/")
def home():
    return "<h1>Graph search demo with optimised in-memory traversal</h1>"


@app.route('/paths')
# e.g. http://localhost:5001/paths?start=cfcd208495d565ef66e7dff9f98764da&end=000871c1fc726f0b52dc86a4eeb027de&dist=4
def paths():
    start_id = request.args.get('start').lower()
    end_id = request.args.get('end').lower()
    distance = int(request.args.get('dist'))
    logging.info(
        f'Requests path from {start_id} to {end_id} with distance = {distance}')
    paths, time_elapsed = graph.get_all_paths(start_id, end_id, distance)
    result = {
        '_data_source': graph.repo_type,
        '_search_details': f'Find path between {start_id} and {end_id} with distance = {distance}',
        '_search_performance': f'Search completed in {time_elapsed} seconds.',
        'paths_found': len(paths),
        'valid_paths': paths
    }
    return jsonify(result), 200


@app.route('/radial')
# e.g. http://localhost:5001/radial?node=cfcd208495d565ef66e7dff9f98764da&degree=3&mode=showdata
def radial():
    """ Runs in two modes:
    LIVE_MODE: returns actual data from the traversal
    BENCHMARK_MODE: compute the result graph without returning data to the front end for
    benchmarking without the network transfer component
    """
    node_id = request.args.get('node').lower()
    degree = int(request.args.get('degree'))
    mode = request.args.get('mode', BENCHMARK_MODE).lower()
    logging.info(
        f'Requests radial graph from {node_id} within {degree} degree(s)')
    node_radial_data, time_elapsed = graph.get_radial_data(
        node_id, degree)
    result = {
        '_data_source': graph.repo_type,
        '_search_details': f'Find node {node_id} neighborhood within {degree} degree(s)',
        '_search_performance': f'Search completed in {time_elapsed} seconds.',
        '_search_result': f"Constructed a graph with a total of {node_radial_data.get('edge_count')} paths",
    }
    if mode == LIVE_MODE:
        result.update({
            'node_radial': node_radial_data.get('graph'),
        })
        logging.info("Live mode: show data")
    return jsonify(result), 200


if __name__ == "__main__":
    global graph
    # For Docker-Compose launch option
    data_source = sys.argv[1]
    graph = Graph(data_source)
    app.run(host='0.0.0.0', port=5001, debug=False)
