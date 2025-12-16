from __future__ import annotations
from contextvars import ContextVar
from typing import Optional
from typing_extensions import Literal
from djin.containers.core import (
    ID,
    Container,
    Stowable,
    Ref,
    Warehouse,
)
from djin.math_objects.framed import Pose3D, Transformable3D
from djin.transforms.transform3d import (
    to_ground_frame,
    to_parent_frame,
    to_target_frame,
)
from djin.base import immutable

current_frame_registry = ContextVar("frame_registry", default=None)

__all__ = [
    "Frame",
]


@immutable
class Frame(Transformable3D[tuple[Pose3D]], Stowable):
    type: Literal["Frame"] = "Frame"
    parent_id: Optional[ID] = None  # Parent frame
    pose: Pose3D

    @property
    def parent(self) -> Optional[Ref[Frame]]:
        return Ref[Frame](id=self.parent_id) if self.parent_id is not None else None

    def get_component_field_names(self) -> tuple[str, ...]:
        return ("pose",)

    def get_components(self) -> tuple[Pose3D]:
        return (self.pose,)

    def get_components_in_parent_frame(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        return (
            to_parent_frame(
                transformable=self.pose,
                starting_frame=starting_frame,
                warehouse=warehouse,
            ),
        )

    def get_components_in_target_frame(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        return (
            to_target_frame(
                transformable=self.pose,
                starting_frame=starting_frame,
                target_frame=target_frame,
                warehouse=warehouse,
            ),
        )

    def to_parent_frame(
        self,
        warehouse: Optional[Warehouse] = None,
    ):
        return to_parent_frame(
            transformable=self,
            starting_frame=self.parent_id,
            warehouse=warehouse,
        )

    def to_ground_frame(
        self,
        warehouse: Optional[Warehouse] = None,
    ):
        return to_ground_frame(
            transformable=self,
            starting_frame=self.parent_id,
            warehouse=warehouse,
        )

    def to_target_frame(
        self,
        target_frame: Optional[ID | Container[Frame]],
        warehouse: Optional[Warehouse] = None,
    ):
        return to_target_frame(
            transformable=self,
            starting_frame=self.parent_id,
            target_frame=target_frame,
            warehouse=warehouse,
        )
