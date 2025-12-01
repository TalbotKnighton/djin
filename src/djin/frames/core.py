from __future__ import annotations
from contextvars import ContextVar
from typing import Any, Optional, Self
import pydantic as pyd
from typing_extensions import Literal
from djin.containers.core import Container, Ref, Warehouse
from djin.math_objects.framed import Pose3D
from djin.base import immutable

current_frame_registry = ContextVar("frame_registry", default=None)

__all__ = [
    "Frame",
]


@immutable
class Frame(pyd.BaseModel):
    type_discriminator: Literal["Frame"] = "Frame"
    pose: Pose3D
    parent_ref: Optional[Ref[Frame]] = None  # Parent frame

    def get_parent_optional(
        self,
        warehouse: Warehouse[Frame | Any],
    ) -> Optional[Container[Frame]]:
        if self.parent_ref is None:
            return None
        else:
            return self.parent_ref.get_optional(warehouse=warehouse)

    def unpack_parent_optional(
        self, warehouse: Warehouse[Frame | Any]
    ) -> Optional[Frame]:
        parent_container = self.get_parent_optional(warehouse=warehouse)
        if parent_container is None:
            return None
        else:
            return parent_container.contents

    def to_parent_frame(
        self,
    ) -> Self:
        parent = self.unpack_parent_optional(warehouse=None)  # TODO real warehouse
        if parent is None:
            return self.model_copy(deep=True)
        else:
            return type(self)(
                pose=self.pose.to_parent_frame(starting_frame=self),
                parent_ref=parent.parent_ref,
            )

    def to_ground_frame(
        self,
    ) -> Self:
        parent = self.unpack_parent_optional(warehouse=None)  # TODO real warehouse
        if parent is None:
            return self.model_copy(deep=True)
        else:
            return type(self)(
                pose=self.pose.to_ground_frame(starting_frame=self),
                parent_ref=None,
            )

    def to_target_frame(
        self,
        target_frame_ref: Ref[Frame],
    ) -> Self:
        parent = self.unpack_parent_optional(warehouse=None)  # TODO real warehouse
        target_frame = target_frame_ref.unpack(warehouse=None)  # TODO real warehouse
        if parent is None:
            return self.model_copy(deep=True)
        else:
            return type(self)(
                pose=self.pose.to_target_frame(
                    starting_frame=self,
                    target_frame=target_frame,
                ),
                parent_ref=target_frame_ref,
            )
