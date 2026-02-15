"""
Named Selections — CAD-style grouping of geometric entities.
Allows users to name and manage selections of faces, edges, vertices.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SelectionEntityType(str, Enum):
    """Type of geometric entity in a selection."""
    FACE = "face"
    EDGE = "edge"
    VERTEX = "vertex"
    NODE = "node"
    ELEMENT = "element"


class NamedSelection(BaseModel):
    """A named group of geometric entities."""
    id: str = Field(..., description="Unique selection ID")
    name: str = Field(..., description="User-friendly name (e.g., 'Unterseite', 'Bohrung links')")
    entity_type: SelectionEntityType = Field(..., description="Type of entities in this selection")
    entity_indices: List[int] = Field(default_factory=list, description="Indices of selected entities")
    color: str = Field("#ff6b6b", description="Display color (hex)")
    visible: bool = Field(True, description="Whether to show in viewport")
    locked: bool = Field(False, description="Prevent accidental modification")
    metadata: dict = Field(default_factory=dict, description="Additional info (area, centroid, etc.)")


class NamedSelectionSet(BaseModel):
    """Collection of all named selections for a model."""
    selections: List[NamedSelection] = Field(default_factory=list)

    def get_by_name(self, name: str) -> Optional[NamedSelection]:
        for s in self.selections:
            if s.name == name:
                return s
        return None

    def get_by_id(self, sel_id: str) -> Optional[NamedSelection]:
        for s in self.selections:
            if s.id == sel_id:
                return s
        return None

    def get_by_type(self, entity_type: SelectionEntityType) -> List[NamedSelection]:
        return [s for s in self.selections if s.entity_type == entity_type]
