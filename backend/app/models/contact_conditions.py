"""
Contact Conditions — Define interactions between surfaces.
Supports bonded, frictionless, frictional, and no-separation contacts.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ContactType(str, Enum):
    """Type of contact interaction."""
    BONDED = "bonded"           # Surfaces glued together (no relative motion)
    FRICTIONLESS = "frictionless"  # Free sliding, no friction
    FRICTIONAL = "frictional"      # Sliding with friction coefficient
    NO_SEPARATION = "no_separation"  # Can slide but not separate


class ContactFormulation(str, Enum):
    """Numerical formulation for contact."""
    PENALTY = "penalty"
    AUGMENTED_LAGRANGE = "augmented_lagrange"
    PURE_LAGRANGE = "pure_lagrange"


class ContactPair(BaseModel):
    """A contact pair between two surfaces."""
    id: str = Field(..., description="Unique contact ID")
    name: str = Field("Kontakt", description="User-friendly name")
    contact_type: ContactType = Field(ContactType.BONDED, description="Type of contact")
    formulation: ContactFormulation = Field(ContactFormulation.PENALTY, description="Numerical formulation")

    # Surfaces (reference named selections by ID)
    master_selection_id: str = Field(..., description="Named selection ID for master surface")
    slave_selection_id: str = Field(..., description="Named selection ID for slave/target surface")

    # Parameters
    friction_coefficient: float = Field(0.0, ge=0.0, le=2.0, description="Friction coefficient (only for frictional)")
    normal_stiffness: float = Field(1.0, gt=0.0, description="Contact normal stiffness factor")
    penetration_tolerance: float = Field(0.0, ge=0.0, description="Allowed penetration tolerance")

    # State
    active: bool = Field(True, description="Whether this contact is active")
    visible: bool = Field(True, description="Show in viewport")
    color: str = Field("#ffa726", description="Display color (hex)")


class ContactConditionSet(BaseModel):
    """Collection of all contact conditions."""
    contacts: List[ContactPair] = Field(default_factory=list)

    def get_by_id(self, contact_id: str) -> Optional[ContactPair]:
        for c in self.contacts:
            if c.id == contact_id:
                return c
        return None

    def validate_selections(self, available_selection_ids: List[str]) -> List[str]:
        """Check that all referenced selections exist. Returns list of errors."""
        errors = []
        for c in self.contacts:
            if c.master_selection_id not in available_selection_ids:
                errors.append(f"Kontakt '{c.name}': Master-Selektion '{c.master_selection_id}' nicht gefunden")
            if c.slave_selection_id not in available_selection_ids:
                errors.append(f"Kontakt '{c.name}': Slave-Selektion '{c.slave_selection_id}' nicht gefunden")
        return errors
