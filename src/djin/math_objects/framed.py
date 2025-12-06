from __future__ import annotations
from abc import ABC, abstractmethod

from typing_extensions import deprecated
from typing import Any, Literal, TypeVar, Generic, Optional, Self, TYPE_CHECKING
from djin.math_objects.frameless import VectorR3, Quaternion
from djin.base import pydantic as pyd, immutable
from djin.containers.core import ID, Container, Ref, Warehouse, get_warehouse


if TYPE_CHECKING:
    from djin.frames.core import Frame

T = TypeVar("T", bound=tuple)


@immutable
class Transformable3D(pyd.BaseModel, Generic[T]):
    @abstractmethod
    def get_components(self) -> T:
        raise NotImplementedError("You must implement this method")

    @abstractmethod
    def get_component_field_names(
        self,
    ) -> tuple[str, ...]:
        raise NotImplementedError()

    @abstractmethod
    def get_components_in_parent_frame(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> T:
        raise NotImplementedError()

    @abstractmethod
    def get_components_in_target_frame(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> T:
        raise NotImplementedError()

    def with_new_components(self, components: T) -> Self:
        if not isinstance(self, pyd.BaseModel):
            raise ValueError(
                f"{Transformable3D.__qualname__} must be a mixin for a child of `pydantic.BaseModel`"
            )
        return self.model_copy(
            deep=True,
            update={
                fname: c
                for fname, c in zip(
                    self.get_component_field_names(),
                    components,
                )
            },
        )


TF = TypeVar("TF", bound=Transformable3D)


def _get_transformable_object(
    transformable: TF | ID | Container[TF],
    warehouse: Optional[Warehouse] = None,
) -> TF:
    if isinstance(transformable, Transformable3D):
        return transformable
    elif isinstance(transformable, Container):
        return transformable.contents
    else:
        return get_warehouse(warehouse=warehouse).unpack(id=transformable)


def to_parent_frame(
    transformable: TF | ID | Container[TF],
    starting_frame: Optional[ID | Container[Frame]] = None,
    warehouse: Optional[Warehouse] = None,
) -> TF:
    from djin.frames.core import Frame

    tf = _get_transformable_object(
        transformable=transformable,
        warehouse=warehouse,
    )
    if starting_frame is None:  # Ground is parent of all frames
        return tf.model_copy(deep=True)
    else:
        return tf.with_new_components(
            components=tf.get_components_in_parent_frame(
                starting_frame=(
                    Ref[Frame](id=starting_frame).get()
                    if not isinstance(starting_frame, Container)
                    else starting_frame
                ),
                warehouse=warehouse,
            )
        )


def to_ground_frame(
    transformable: TF | ID | Container[TF],
    starting_frame: Optional[ID | Container[Frame]],
    warehouse: Optional[Warehouse] = None,
) -> TF:
    from djin.frames.core import Frame

    tf = _get_transformable_object(
        transformable=transformable,
        warehouse=warehouse,
    )
    if starting_frame is None:
        return tf.model_copy(deep=True)
    else:
        parent = (
            starting_frame.contents.parent.get(warehouse=warehouse)
            if isinstance(starting_frame, Container)
            else Ref[Frame](id=starting_frame).get(warehouse=warehouse)
        )
        up_one_level = to_parent_frame(
            transformable=tf,
            starting_frame=starting_frame,
            warehouse=warehouse,
        )
        return to_ground_frame(
            transformable=up_one_level,
            starting_frame=parent,
            warehouse=warehouse,
        )


def to_target_frame(
    transformable: TF | ID | Container[TF],
    starting_frame: Optional[ID | Container[Frame]],
    target_frame: Optional[ID | Container[Frame]],
    warehouse: Optional[Warehouse] = None,
) -> TF:
    from djin.frames.core import Frame

    tf = _get_transformable_object(
        transformable=transformable,
        warehouse=warehouse,
    )
    if target_frame is None:
        return to_ground_frame(
            transformable=tf,
            starting_frame=starting_frame,
            warehouse=warehouse,
        )
    else:
        return tf.with_new_components(
            components=tf.get_components_in_target_frame(
                starting_frame=(
                    Ref[Frame](id=starting_frame).get()
                    if not isinstance(starting_frame, Container)
                    else starting_frame
                ),
                target_frame=(
                    Ref[Frame](id=target_frame).get()
                    if not isinstance(target_frame, Container)
                    else target_frame
                ),
                warehouse=warehouse,
            )
        )


@immutable
class Vector3D(Transformable3D[tuple[VectorR3]]):
    type: Literal["Vector3D"] = "Vector3D"
    vector: VectorR3

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
    vector: VectorR3

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
    quaternion: Quaternion

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
