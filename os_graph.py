# Copyright 2023 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

import csv
import logging
import pickle
import time
import traceback
from collections import deque
from functools import lru_cache, wraps

from configure_logger import init_logger
from mem_repo import MemRepo

# from memory_profiler import profile


LOAD_COMPRESSION_MAPS = True
# If True, use a translation map to accept API inputs in the original graph edge/node ids
# If False, the internal graph is queried with numerical incremental id generated at graph load time
PATH_PICKLED_GRAPH = './graph.pickle'
PATH_PICKLED_UUID_TO_COMPRESSED = './graph_uuid_to_compressed.pickle'
PATH_PICKLED_COMPRESSED_TO_UUID = './graph_compressed_to_uuid.pickle'

init_logger()


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_time_str = f'{total_time:.4f}'
        logging.info(
            f'Function {func.__name__}{args} {kwargs} Took {total_time_str} seconds')
        return result, total_time_str
    return timeit_wrapper


class Graph:

    def __init__(self, data_src=None, verbose=False):
        self.repo = MemRepo()
        self.repo_type = "in-memory"

        start_time = time.perf_counter()

        # Attempt to load constructed graph from disk
        graph_loaded = self.__load_graph_from_pickle()

        # Load data from file cache into mem db
        if not graph_loaded:
            self.load_graph_data(data_src)
            self.__pickle_graph()

        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_time_str = f'{total_time:.4f}'
        logging.info(f"Graph loading time: {total_time_str}")
        logging.info(
            f"Graph in-memory size: {self.repo.mem_size()} bytes")

    def __pickle_graph(self):
        # A quicker way to load the graph into memory from file
        # Assets need to be built to disk outside containers
        with open(PATH_PICKLED_GRAPH, 'wb') as file:
            pickle.dump(self.repo.adj_matrix, file,
                        protocol=pickle.HIGHEST_PROTOCOL)
        if LOAD_COMPRESSION_MAPS:
            # Save the mapping between original ids and compressed ids
            with open(PATH_PICKLED_UUID_TO_COMPRESSED, 'wb') as file:
                pickle.dump(self.repo.uuid_to_compressed, file,
                            protocol=pickle.HIGHEST_PROTOCOL)
            with open(PATH_PICKLED_COMPRESSED_TO_UUID, 'wb') as file:
                pickle.dump(self.repo.compressed_to_uuid, file,
                            protocol=pickle.HIGHEST_PROTOCOL)

    def __load_graph_from_pickle(self):
        # A quicker way to load the graph into memory from file
        # Assets need to be built to disk outside containers
        try:
            with open(PATH_PICKLED_GRAPH, 'rb') as file:
                self.repo.adj_matrix = pickle.load(file)
            if LOAD_COMPRESSION_MAPS:
                with open(PATH_PICKLED_UUID_TO_COMPRESSED, 'rb') as file:
                    self.repo.uuid_to_compressed = pickle.load(file)
                with open(PATH_PICKLED_COMPRESSED_TO_UUID, 'rb') as file:
                    self.repo.compressed_to_uuid = pickle.load(file)
            logging.info("Graph loaded from pickle")
            return True
        except Exception:
            logging.warning("Failed to load graph from pickle")
            logging.warning(traceback.format_exc())
            return False

    @lru_cache
    def __find_paths(self, origin: str, dest: str, max_dist: int):
        """ DFS backtracking to find all paths up to max_dist from the origin
        node. Since this implementation is memory heavy, use DFS to reduce queue 
        size. As we are looking for all possible paths and not the shortest path, 
        traversal time complexity is the same as BFS """
        # Find paths up to max_dist from a radial graph json
        solutions = []
        if LOAD_COMPRESSION_MAPS:
            # Mapping between original edge ids and compressed edge ids
            origin = self.repo.get_compressed(origin)
            dest = self.repo.get_compressed(dest)

        def find_paths_dfs(node, cur_degrees, partial_path):
            connections = self.__get_all_connections(node)
            logging.debug(
                f"Getting connections of {node}: {connections}")
            if cur_degrees > max_dist or not connections:
                return
            for connection in connections:
                to_node_id = connection.split(":")[0]
                logging.debug(f"Currently at {to_node_id}")
                partial_path.append(to_node_id)
                if to_node_id == dest:
                    solutions.append(partial_path.copy())
                find_paths_dfs(
                    to_node_id,
                    cur_degrees + 1,
                    partial_path
                )
                partial_path.pop()

        find_paths_dfs(
            origin,
            1,
            [origin]
        )
        logging.debug(solutions)
        return solutions

    # Uncomment the decorator in the next line to enable loading memory profiling
    # @profile
    def load_graph_data(self, path: str, bidirectional: bool = True):
        """ Load graph from CSV file
        """

        logging.info(f"bidirectional mode is {bidirectional}")
        try:
            with open(path, 'r', encoding='utf-8-sig') as read_obj:
                csv_reader = csv.DictReader(read_obj)
                size = 0
                row_count = 0
                for row in csv_reader:
                    if row_count % 10000 == 0:
                        logging.info(f"Processed {row_count} rels")
                    row_count += 1
                    src = row['entity_from_guid'].lower()
                    dest = row['entity_to_guid'].lower()
                    relation = row['relationship_type']
                    rel_id = row['relationship_id']
                    # Forward
                    self.repo.index(src, dest, relation, rel_id)
                    size += 1
                    if bidirectional:
                        # Backward - create a reverse edge
                        self.repo.index(
                            dest, src, f"-{relation}", f"-{rel_id}")
                        size += 1
                logging.info(f"read {size} lines of relation data")
            logging.info("loaded {} nodes".format(self.repo.size()))
        except FileNotFoundError as error:
            logging.error(f"Could not find file: {path}")
            raise error
        except csv.Error as error:
            logging.error(f"Error parsing CSV file: {path}")
            raise error

    @lru_cache
    def __get_all_connections(self, node: str):
        return self.repo.get(node)

    def __compute_radial_data(self, source: str, degrees: int):
        """ BFS algorithm to follow all edges up to max_dist from the origin
        node """

        visit_count = 0
        cur_deg = 0
        queue = deque()

        def find_radial_bfs(edge_set):
            nonlocal visit_count
            nonlocal cur_deg
            nonlocal degrees
            thread_node_processed_count = 0
            repeated_edges = 0

            while queue:
                node = queue.popleft()
                if cur_deg >= degrees:
                    logging.debug(
                        f"break at degree = {cur_deg - 1}, exceed query degree limit")
                    break
                if node is None:
                    cur_deg += 1
                    logging.debug(
                        f"degree = {cur_deg - 1}, visited {visit_count} nodes so far")
                    queue.append(None)
                    continue
                if node in seen_nodes:
                    continue
                thread_node_processed_count += 1
                visit_count += 1
                node_id = node
                seen_nodes.update({node_id: True})
                connections = self.__get_all_connections(node_id)
                if connections:
                    for connection in connections:
                        # Get encoded data in the edge
                        to_node_id, relation_type, relationship_id = tuple(
                            connection.split(":"))
                        edge_data = (node_id, to_node_id,
                                     relation_type, relationship_id)
                        if not seen_edges.get(relationship_id, None):
                            # Mark as seen
                            seen_edges.update({relationship_id: True})
                            edge_set.add(edge_data)
                        else:
                            repeated_edges += 1
                        if to_node_id not in seen_nodes:
                            # Add to todo queue
                            queue.append(to_node_id)
            logging.debug(
                f"End after processing {thread_node_processed_count} nodes")

        if LOAD_COMPRESSION_MAPS:
            source = self.repo.get_compressed(source)
            logging.debug(f"Compressed source value = {source}")

        queue.append(source)
        queue.append(None)
        edge_set = set()
        seen_edges = {}
        seen_nodes = {}

        find_radial_bfs(edge_set)

        return {
            "graph": list(edge_set),
            "edge_count": len(edge_set),
        }

    @ timeit
    def get_radial_data(self, source: str, degrees: int) -> dict:
        return self.__compute_radial_data(source, degrees)

    @ timeit
    def get_all_paths(self, source: str, destination: str, degrees: int) -> list[list[str]]:
        return self.__find_paths(source, destination, degrees)
