from __future__ import annotations
from contextvars import ContextVar
from typing import Any, Optional, Self
import pydantic as pyd
from typing_extensions import Literal
from djin.containers.core import ID, Container, Ref, Warehouse
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
    parent_id: Optional[ID] = None  # Parent frame

    @property
    def parent_ref(self) -> Optional[Ref[Self]]:
        return None if self.parent_id is None else Ref[Self](id=self.parent_id)

    @property
    def get_parent(self) -> Container[Self]:
        
    # def get_parent_optional(
    #     self,
    #     warehouse: Warehouse[Frame | Any],
    # ) -> Optional[Container[Self]]:
    #     if self.parent_ref is None:
    #         return None
    #     else:
    #         return self.parent_ref.get_optional(warehouse=warehouse)

    # def unpack_parent_optional(
    #     self, warehouse: Warehouse[Self | Any]
    # ) -> Optional[Frame]:
    #     parent_container = self.get_parent_optional(warehouse=warehouse)
    #     if parent_container is None:
    #         return None
    #     else:
    #         return parent_container.contents

    def to_parent_frame(
        self,
    ) -> Self:
        r = self.parent_ref
        if r is None:
            return self.model_copy(deep=True)
        else:
            parent = r.unpack(warehouse=None)
            new_ref = parent.parent_ref
            return type(self)(
                pose=self.pose.to_parent_frame(starting_frame=self),
                parent_id=getattr(new_ref, "id", None),
            )

    def to_ground_frame(
        self,
    ) -> Self:
        r = self.parent_ref
        if r is None:
            return self.model_copy(deep=True)
        else:
            parent = r.unpack(warehouse=None)
            if parent is None:
                return self.model_copy(deep=True)
            else:
                return type(self)(
                    pose=self.pose.to_ground_frame(starting_frame=self),
                    parent_id=None,
                )

    def to_target_frame(
        self,
        target_frame_id: ID,
    ) -> Self:
        r = self.parent_ref
        if r is None:
            return self.model_copy(deep=True)
        else:
            parent = r.unpack(warehouse=None)
            if parent is None:
                return self.model_copy(deep=True)
            else:
                target_frame_container = Ref[Self](id=target_frame_id).get(
                    warehouse=None
                )  # TODO real warehouse
                target_frame = target_frame_container.contents
                return type(self)(
                    pose=self.pose.to_target_frame(
                        starting_frame=self,
                        target_frame=target_frame,
                    ),
                    parent_id=target_frame_container.id,
                )
