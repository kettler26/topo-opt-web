"""
Boundary condition models — Level 3: Full CAD-style.
Supports named-selection-based BCs, contact conditions, and advanced loads.
"""
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class Vector3D(BaseModel):
    """3D vector."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class BCType(str, Enum):
    """Boundary condition types (Level 3)."""
    FIXATION = "fixation"
    FORCE = "force"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    DISPLACEMENT = "displacement"
    MOMENT = "moment"
    REMOTE_FORCE = "remote_force"
    BEARING_LOAD = "bearing_load"
    CONVECTION = "convection"
    HEAT_FLUX = "heat_flux"


class BCApplicationMethod(str, Enum):
    """How a BC is applied to geometry."""
    NODE_IDS = "node_ids"           # Direct node selection
    FACE_IDS = "face_ids"           # Direct face selection
    NAMED_SELECTION = "named_selection"  # Via named selection
    COORDINATE_RANGE = "coordinate_range"  # By coordinate box


class CoordinateRange(BaseModel):
    """Axis-aligned bounding box for coordinate-based selection."""
    min_point: Vector3D = Field(default_factory=Vector3D)
    max_point: Vector3D = Field(default_factory=lambda: Vector3D(x=1, y=1, z=1))


class BaseBoundaryCondition(BaseModel):
    """Base class for all boundary conditions."""
    id: str = Field(..., description="Unique BC ID")
    name: str = Field("Randbedingung", description="Display name")
    bc_type: BCType
    application_method: BCApplicationMethod = Field(BCApplicationMethod.NAMED_SELECTION)
    named_selection_id: Optional[str] = Field(None, description="Named selection reference")
    node_ids: List[int] = Field(default_factory=list)
    face_ids: List[int] = Field(default_factory=list)
    coordinate_range: Optional[CoordinateRange] = None
    active: bool = Field(True)
    visible: bool = Field(True)
    color: str = Field("#4fc3f7")


class FixationBC(BaseBoundaryCondition):
    """Fixed support — constrains DOFs."""
    bc_type: BCType = BCType.FIXATION
    fix_x: bool = True
    fix_y: bool = True
    fix_z: bool = True
    fix_rx: bool = False  # Rotational DOFs (for shell/beam)
    fix_ry: bool = False
    fix_rz: bool = False


class DisplacementBC(BaseBoundaryCondition):
    """Prescribed displacement."""
    bc_type: BCType = BCType.DISPLACEMENT
    displacement: Vector3D = Field(default_factory=Vector3D)
    coordinate_system: str = Field("global", description="Coordinate system (global/cylindrical/local)")


class ForceBC(BaseBoundaryCondition):
    """Applied force."""
    bc_type: BCType = BCType.FORCE
    direction: Vector3D = Field(default_factory=lambda: Vector3D(y=-1))
    magnitude: float = Field(1000.0, description="Force in Newtons")
    distribution: str = Field("uniform", description="uniform / per_node / total")


class MomentBC(BaseBoundaryCondition):
    """Applied moment/torque."""
    bc_type: BCType = BCType.MOMENT
    axis: Vector3D = Field(default_factory=lambda: Vector3D(z=1))
    magnitude: float = Field(100.0, description="Moment in N·m")


class RemoteForceBC(BaseBoundaryCondition):
    """Force applied at a remote point, transferred to surface."""
    bc_type: BCType = BCType.REMOTE_FORCE
    application_point: Vector3D = Field(default_factory=Vector3D)
    force: Vector3D = Field(default_factory=lambda: Vector3D(y=-1000))
    behavior: str = Field("deformable", description="rigid / deformable")


class PressureBC(BaseBoundaryCondition):
    """Surface pressure load."""
    bc_type: BCType = BCType.PRESSURE
    magnitude: float = Field(1e5, description="Pressure in Pascals")
    direction: str = Field("normal", description="normal / x / y / z")


class BearingLoadBC(BaseBoundaryCondition):
    """Bearing load (distributed radial load on cylindrical face)."""
    bc_type: BCType = BCType.BEARING_LOAD
    magnitude: float = Field(5000.0, description="Total bearing load in Newtons")
    axis: Vector3D = Field(default_factory=lambda: Vector3D(z=1))


class TemperatureBC(BaseBoundaryCondition):
    """Fixed temperature."""
    bc_type: BCType = BCType.TEMPERATURE
    temperature: float = Field(293.15, description="Temperature in Kelvin")


class ConvectionBC(BaseBoundaryCondition):
    """Convection heat transfer on surface."""
    bc_type: BCType = BCType.CONVECTION
    film_coefficient: float = Field(10.0, description="Film coefficient in W/(m²·K)")
    ambient_temperature: float = Field(293.15, description="Ambient temperature in Kelvin")


class HeatFluxBC(BaseBoundaryCondition):
    """Applied heat flux on surface."""
    bc_type: BCType = BCType.HEAT_FLUX
    magnitude: float = Field(1000.0, description="Heat flux in W/m²")


# Union type for all BCs
AnyBoundaryCondition = Union[
    FixationBC, DisplacementBC, ForceBC, MomentBC,
    RemoteForceBC, PressureBC, BearingLoadBC,
    TemperatureBC, ConvectionBC, HeatFluxBC,
]


class BoundaryConditionSet(BaseModel):
    """Collection of all boundary conditions for an optimization."""
    conditions: List[AnyBoundaryCondition] = Field(default_factory=list)

    def get_by_type(self, bc_type: BCType) -> list:
        return [c for c in self.conditions if c.bc_type == bc_type]

    def get_by_id(self, bc_id: str) -> Optional[AnyBoundaryCondition]:
        for c in self.conditions:
            if c.id == bc_id:
                return c
        return None

    def get_active(self) -> list:
        return [c for c in self.conditions if c.active]
