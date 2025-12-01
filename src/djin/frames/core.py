from __future__ import annotations
from contextvars import ContextVar
from typing import Any, Optional, Self
import pydantic as pyd
from typing_extensions import Literal
from djin.containers.core import ID, Stowable, Ref, Warehouse, get_warehouse
from djin.math_objects.framed import Pose3D
from djin.base import immutable

current_frame_registry = ContextVar("frame_registry", default=None)

__all__ = [
    "Frame",
]


@immutable
class Frame(Stowable):
    type: Literal["Frame"] = "Frame"
    pose: Pose3D
    parent_id: Optional[ID] = None  # Parent frame

    @property
    def parent(self) -> Ref[Frame]:
        return Ref[Frame](id=self.parent_id)

    def to_parent_frame(
        self,
        warehouse: Optional[Warehouse] = None,
    ) -> Self:
        with get_warehouse(warehouse).set_context():
            if self.parent_id is None:
                return self.model_copy(deep=True)
            else:
                parent = self.parent.unpack()
                return type(self)(
                    pose=self.pose.to_parent_frame(starting_frame=self),
                    parent_id=getattr(parent.parent, "id", None),
                )

    def to_ground_frame(
        self,
        warehouse: Optional[Warehouse] = None,
    ) -> Self:
        with get_warehouse(warehouse).set_context():
            if self.parent_id is None:
                return self.model_copy(deep=True)
            else:
                parent = self.parent.unpack()
                if parent is None:
                    return self.model_copy(deep=True)
                else:
                    return type(self)(
                        pose=self.pose.to_ground_frame(starting_frame=self),
                        parent_id=None,
                    )

    def to_target_frame(
        self,
        target_frame: ID,
        warehouse: Optional[Warehouse] = None,
    ) -> Self:
        with get_warehouse(warehouse).set_context() as wh:
            if self.parent_id is None:
                return self.model_copy(deep=True)
            else:
                parent = self.parent.unpack()
                if parent is None:
                    return self.model_copy(deep=True)
                else:
                    tf = Ref[Frame](id=target_frame).get()
                    return type(self)(
                        pose=self.pose.to_target_frame(
                            starting_frame=self,
                            target_frame=tf.contents,
                        ),
                        parent_id=tf.id,
                    )
