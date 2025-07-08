from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class MutationType(Enum):
    INSERT = "insert"
    REPLACE = "replace"
    DELETE = "delete"


@dataclass
class Individual:
    """Base class for genetic algorithm individuals"""

    genes: Any
    fitness: Optional[float] = None

    def __hash__(self):
        return hash(str(self.genes))
