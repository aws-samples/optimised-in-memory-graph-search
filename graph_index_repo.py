# Copyright 2023 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

from abc import ABC, abstractmethod


class GraphIndexRepo(ABC):

    @abstractmethod
    def get(self, id: str):
        pass

    @abstractmethod
    def index(self, source: str, dest: dict, relationship: str, relationship_id: str):
        pass
