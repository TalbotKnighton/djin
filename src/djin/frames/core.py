from __future__ import annotations
from contextvars import ContextVar
from typing import Optional, Self, TypeVar
import pydantic as pyd
from typing_extensions import Literal
from djin.containers.core import (
    ID,
    Container,
    Stowable,
    Ref,
    Warehouse,
    get_warehouse,
)
from djin.math_objects.framed import Pose3D, Transformable3D
from djin.base import immutable

current_frame_registry = ContextVar("frame_registry", default=None)

__all__ = [
    "Frame",
]


@immutable
class Frame(Transformable3D[Pose3D], Stowable):
    type: Literal["Frame"] = "Frame"
    parent_id: Optional[ID] = None  # Parent frame

    @property
    def pose(self):
        return self.components

    @property
    def parent(self) -> Ref[Frame]:
        return Ref[Frame](id=self.parent_id)

    # def to_parent_frame(
    #     self,
    #     warehouse: Optional[Warehouse] = None,
    # ) -> Self:
    #     with get_warehouse(warehouse).set_context():
    #         if self.parent_id is None:
    #             return self.model_copy(deep=True)
    #         else:
    #             parent = self.parent.unpack()
    #             return type(self)(
    #                 pose=self.pose.to_parent_frame(starting_frame=self),
    #                 parent_id=getattr(parent.parent, "id", None),
    #             )

    # def to_ground_frame(
    #     self,
    #     warehouse: Optional[Warehouse] = None,
    # ) -> Self:
    #     with get_warehouse(warehouse).set_context():
    #         if self.parent_id is None:
    #             return self.model_copy(deep=True)
    #         else:
    #             parent = self.parent.unpack()
    #             if parent is None:
    #                 return self.model_copy(deep=True)
    #             else:
    #                 return type(self)(
    #                     pose=self.pose.to_ground_frame(starting_frame=self),
    #                     parent_id=None,
    #                 )

    # def to_target_frame(
    #     self,
    #     target_frame: ID | Container[Frame],
    #     warehouse: Optional[Warehouse] = None,
    # ) -> Self:
    #     if not isinstance(target_frame, Container):
    #         tf = Ref[Frame](id=target_frame).get(warehouse=warehouse)
    #     else:
    #         tf = target_frame
    #     if self.parent_id == tf.id:
    #         return self.model_copy(deep=True)
    #     else:
    #         return self.model_copy(
    #             pose=self.pose.to_target_frame(
    #                 starting_frame=self,
    #                 target_frame=tf.contents,
    #             ),
    #             parent_id=tf.id,
    #         )

    def _to_parent_frame_components(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> Pose3D:
        return self.pose.to_parent_frame(
            starting_frame=starting_frame,
            warehouse=warehouse,
        )

    def _to_target_frame_components(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> Pose3D:
        return self.pose.to_target_frame(
            starting_frame=starting_frame,
            target_frame=target_frame,
            warehouse=warehouse,
        )
