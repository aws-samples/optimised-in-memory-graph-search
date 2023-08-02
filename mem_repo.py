# Copyright 2023 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

import sys
from collections import defaultdict

import numpy

from graph_index_repo import GraphIndexRepo


class MemRepo(GraphIndexRepo):

    adj_matrix = defaultdict(list)
    uuid_to_compressed: dict = {}
    compressed_to_uuid: dict = {}
    current_id = 0
    RADIX = 36

    def __next(self):
        self.current_id += 1
        return numpy.base_repr(self.current_id, self.__class__.RADIX)

    def get(self, id: str):
        return self.adj_matrix.get(id)

    def get_compressed(self, string: str):
        result = self.uuid_to_compressed.get(string)
        if result is None:
            result = self.__next()
            self.uuid_to_compressed[string] = result
            self.compressed_to_uuid[result] = string
        return result

    def uncompress(self, compressed_string: str):
        return self.compressed_to_uuid[compressed_string]

    def index(self, source: str, dest: str, relationship: str, relationship_id: str):
        compressed_source = self.get_compressed(source)
        compressed_dest = self.get_compressed(dest)
        val = f"{compressed_dest}:{relationship}:{relationship_id}"
        value = self.adj_matrix.get(compressed_source, [])
        value.append(val)
        self.adj_matrix[compressed_source] = value

    def size(self):
        return len(self.adj_matrix)

    def mem_size(self):
        return sys.getsizeof(self.adj_matrix)
