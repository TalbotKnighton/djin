from __future__ import annotations
from contextvars import ContextVar
from typing import Optional, Self
import pydantic as pyd
from typing_extensions import Literal
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
    parent: Optional[Frame] = None  # Parent frame

    def to_parent_frame(
        self,
    ) -> Self:
        if self.parent is None:
            return self.model_copy(deep=True)
        else:
            return type(self)(
                pose=self.pose.to_parent_frame(starting_frame=self),
                parent=self.parent.parent,
            )

    def to_ground_frame(
        self,
    ) -> Self:
        if self.parent is None:
            return self.model_copy(deep=True)
        else:
            return type(self)(
                pose=self.pose.to_ground_frame(starting_frame=self),
                parent=None,
            )

    def to_target_frame(
        self,
        target_frame: Frame,
    ) -> Self:
        if self.parent is None:
            return self.model_copy(deep=True)
        else:
            return type(self)(
                pose=self.pose.to_target_frame(
                    starting_frame=self,
                    target_frame=target_frame,
                ),
                parent=target_frame,
            )
