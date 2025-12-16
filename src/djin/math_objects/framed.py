from __future__ import annotations
from typing import Literal, Optional, TYPE_CHECKING

import pydantic
from djin.math_objects.frameless import Axis, VectorR3, Quaternion
from djin.base import immutable
from djin.containers.core import Container, Warehouse
from djin.transforms.transform3d import (
    Transformable3D,
    to_ground_frame,
    to_parent_frame,
    to_target_frame,
)


if TYPE_CHECKING:
    from djin.frames.core import Frame


@immutable
class Vector3D(Transformable3D[tuple[VectorR3]]):
    type: Literal["Vector3D"] = "Vector3D"
    vector: VectorR3 = pydantic.Field(default_factory=VectorR3)

    def get_components(self):
        return (self.vector,)

    def get_component_field_names(self):
        return ("vector",)

    def get_components_in_parent_frame(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        return (
            VectorR3.from_array(
                array=starting_frame.contents.pose.orientation.quaternion.as_rotation().as_matrix()
                @ self.vector.array
            ),
        )

    def get_components_in_target_frame(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        rotate_to_target_frame_from_ground = (
            to_ground_frame(
                transformable=target_frame.contents,
                starting_frame=starting_frame,
                warehouse=warehouse,
            )
            .pose.orientation.quaternion.as_rotation()
            .inv()
            .as_matrix()
        )
        ground_frame_vector = to_ground_frame(
            transformable=self,
            starting_frame=starting_frame,
            warehouse=warehouse,
        ).vector
        return (
            VectorR3.from_array(
                array=rotate_to_target_frame_from_ground @ ground_frame_vector,
            ),
        )


@immutable
class Point3D(Transformable3D[tuple[VectorR3]]):
    type: Literal["Point3D"] = "Point3D"
    vector: VectorR3 = pydantic.Field(default_factory=VectorR3)

    @classmethod
    def single_axis_displacement(cls, axis: Axis, distance: float):
        return cls(
            vector=VectorR3.single_axis_displacement(
                axis=axis,
                distance=distance,
            )
        )

    def get_component_field_names(self):
        return ("vector",)

    def get_components(self):
        return (self.vector,)

    def get_components_in_parent_frame(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        rotated_vector = to_parent_frame(
            Vector3D(vector=self.vector),
            starting_frame=starting_frame,
            warehouse=warehouse,
        ).vector
        origin_offset = starting_frame.contents.pose.position.vector
        return (rotated_vector + origin_offset,)

    def get_components_in_target_frame(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        rotated_vector = to_target_frame(
            transformable=Vector3D(vector=self.vector),
            starting_frame=starting_frame,
            target_frame=target_frame,
            warehouse=warehouse,
        ).vector
        origin_offset_to_ground_from_start = to_ground_frame(
            transformable=self,
            starting_frame=starting_frame,
        ).vector
        origin_offset_to_target_from_ground = -to_ground_frame(
            transformable=target_frame.contents,
            starting_frame=target_frame,
        ).pose.position.vector
        origin_offset = (
            origin_offset_to_ground_from_start + origin_offset_to_target_from_ground
        )
        return (rotated_vector + origin_offset,)


@immutable
class Orientation3D(Transformable3D[tuple[Quaternion]]):
    type: Literal["Rotation3D"] = "Rotation3D"
    quaternion: Quaternion = pydantic.Field(default_factory=Quaternion)

    @classmethod
    def single_axis_rotation(
        cls,
        axis: Axis,
        angle: float,
        degrees: bool,
    ) -> Orientation3D:
        return cls(
            quaternion=Quaternion.single_axis_rotation(
                axis=axis,
                angle=angle,
                degrees=degrees,
            )
        )

    def get_component_field_names(self):
        return ("quaternion",)

    def get_components(self):
        return (self.quaternion,)

    def get_components_in_parent_frame(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        return (starting_frame.contents.pose.orientation.quaternion * self.quaternion,)

    def get_components_in_target_frame(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        rotate_to_ground_from_starting = to_ground_frame(
            transformable=starting_frame,
            starting_frame=starting_frame,
            warehouse=warehouse,
        ).pose.orientation.quaternion
        rotate_to_target_from_ground = to_ground_frame(
            transformable=target_frame.contents,
            starting_frame=target_frame,
            warehouse=warehouse,
        ).pose.orientation.quaternion.inv()

        return (rotate_to_target_from_ground * rotate_to_ground_from_starting,)


class Pose3D(
    Transformable3D[
        tuple[
            Point3D,
            Orientation3D,
        ]
    ]
):
    type: Literal["Pose3D"] = "Pose3D"
    position: Point3D
    orientation: Orientation3D

    def get_component_field_names(self):
        return ("position", "orientation")

    def get_components(self):
        return (
            self.position,
            self.orientation,
        )

    def get_components_in_parent_frame(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        return (
            to_parent_frame(
                transformable=self.position,
                starting_frame=starting_frame,
                warehouse=warehouse,
            ),
            to_parent_frame(
                transformable=self.orientation,
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
                transformable=self.position,
                starting_frame=starting_frame,
                target_frame=target_frame,
                warehouse=warehouse,
            ),
            to_target_frame(
                transformable=self.orientation,
                starting_frame=starting_frame,
                target_frame=target_frame,
                warehouse=warehouse,
            ),
        )


def _test():
    p = Pose3D(
        position=Point3D(
            vector=VectorR3(
                data=(
                    0,
                    0,
                    0,
                ),
            ),
        ),
        orientation=Orientation3D(
            quaternion=Quaternion(
                data=(
                    0,
                    0,
                    0,
                    1,
                ),
            ),
        ),
    )
    s = p.model_dump_json(indent=4)
    p2 = Pose3D.model_validate_json(s)
    print(p2.model_dump_json(indent=4))


if __name__ == "__main__":
    _test()
