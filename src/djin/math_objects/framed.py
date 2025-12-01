from __future__ import annotations

from typing import Any, Literal, TypeVar, Generic, Optional, Self, TYPE_CHECKING
from djin.math_objects.frameless import VectorR3, Quaternion
from djin.base import pydantic as pyd, immutable
from djin.containers.core import Warehouse, get_warehouse

T = TypeVar("T")

if TYPE_CHECKING:
    from djin.frames.core import Frame


@immutable
class Transformable3D(pyd.BaseModel, Generic[T]):
    components: T

    @pyd.model_validator(mode="before")
    @classmethod
    def drop_computed_fields(cls, data: Any) -> dict[str, Any]:
        """Drop any computed fields to ensure only the necessary data is stored."""
        if isinstance(data, dict):
            return {
                field: value
                for field, value in data.items()
                if field in cls.model_fields
            }
        return data

    def to_parent_frame(
        self,
        starting_frame: Optional[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> Self:
        if starting_frame is None:
            return self.model_copy(deep=True)
        with get_warehouse(warehouse=warehouse).set_context():
            return type(self)(
                components=self._to_parent_frame_components(
                    starting_frame=starting_frame,
                )
            )

    def _to_parent_frame_components(
        self,
        starting_frame: Frame,
    ) -> T:
        raise NotImplementedError()

    def _to_target_frame_components(
        self,
        starting_frame: Frame,
        target_frame: Frame,
    ) -> T:
        raise NotImplementedError()

    def to_target_frame(
        self,
        starting_frame: Optional[Frame],
        target_frame: Optional[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> Self:
        self_in_ground_frame = self.to_ground_frame(starting_frame=starting_frame)
        if target_frame is None:
            return self_in_ground_frame
        else:
            with get_warehouse(warehouse=warehouse).set_context():
                return type(self)(
                    components=self._to_target_frame_components(
                        starting_frame=target_frame,
                        target_frame=target_frame,
                    )
                )

    def to_ground_frame(
        self,
        starting_frame: Optional[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> Self:
        if starting_frame is None:
            return self.model_copy(deep=True)
        else:
            up_one_level = self.to_parent_frame(starting_frame=starting_frame)
            with get_warehouse(warehouse=warehouse).set_context():
                pp = starting_frame.parent.unpack()
            return up_one_level.to_ground_frame(starting_frame=pp)


class Vector3D(Transformable3D[VectorR3]):
    type: Literal["Vector3D"] = "Vector3D"

    def _to_parent_frame_components(
        self,
        starting_frame: Frame,
    ):
        return VectorR3.from_array(
            array=starting_frame.pose.orientation.components.as_rotation().as_matrix()
            @ self.components.array
        )

    def _to_target_frame_components(
        self,
        starting_frame: Frame,
        target_frame: Frame,
    ) -> VectorR3:
        return VectorR3.from_array(
            target_frame.pose.orientation.to_ground_frame(starting_frame=target_frame)
            .components.as_rotation()
            .inv()
            .as_matrix()
            @ self.to_ground_frame(starting_frame=starting_frame).components.array
        )


class Point3D(Transformable3D[VectorR3]):
    type: Literal["Point3D"] = "Point3D"

    def _to_parent_frame_components(
        self,
        starting_frame: Frame,
    ):
        return VectorR3.from_array(
            array=Vector3D(components=self.components)
            .to_parent_frame(starting_frame=starting_frame)
            .components.array
            + starting_frame.pose.position.components.array
        )

    def _to_target_frame_components(
        self,
        starting_frame: Frame,
        target_frame: Frame,
    ) -> VectorR3:
        return VectorR3.from_array(
            Vector3D(components=self.components)
            .to_target_frame(
                starting_frame=starting_frame,
                target_frame=target_frame,
            )
            .components.array
            + self.to_ground_frame(starting_frame=starting_frame).components.array
            - target_frame.pose.position.to_ground_frame(
                starting_frame=target_frame
            ).components.array
        )


class Orientation3D(Transformable3D[Quaternion]):
    type: Literal["Orientation3D"] = "Orientation3D"

    def _to_parent_frame_components(
        self,
        starting_frame: Frame,
    ) -> Quaternion:
        return Quaternion.from_rotation(
            starting_frame.pose.orientation.components.as_rotation()
            * self.components.as_rotation()
        )

    def _to_target_frame_components(
        self,
        starting_frame: Frame,
        target_frame: Frame,
    ) -> Quaternion:
        return Quaternion.from_rotation(
            target_frame.pose.orientation.to_ground_frame(
                starting_frame=target_frame,
            )
            .components.as_rotation()
            .inv()
            * self.to_ground_frame(
                starting_frame=starting_frame
            ).components.as_rotation()
        )


class Pose3D(Transformable3D[tuple[VectorR3, Quaternion]]):
    type: Literal["Pose3D"] = "Pose3D"

    @property
    def position(self):
        return Point3D(components=self.components[0])

    @property
    def orientation(self):
        return Orientation3D(components=self.components[1])

    def _to_parent_frame_components(
        self,
        starting_frame: Frame,
    ) -> tuple[VectorR3, Quaternion]:
        point_components, orientation_components = self.components
        point = Point3D(components=point_components)
        orientation = Orientation3D(components=orientation_components)
        new_point = point.to_parent_frame(starting_frame=starting_frame).components
        new_orientation = orientation.to_parent_frame(
            starting_frame=starting_frame
        ).components
        return (new_point, new_orientation)

    def _to_target_frame_components(
        self,
        starting_frame: Frame,
        target_frame: Frame,
    ) -> tuple[VectorR3, Quaternion]:
        point_components, orientation_components = self.components
        point = Point3D(components=point_components)
        orientation = Orientation3D(components=orientation_components)
        new_point = point.to_target_frame(
            starting_frame=starting_frame,
            target_frame=target_frame,
        ).components
        new_orientation = orientation.to_target_frame(
            starting_frame=starting_frame,
            target_frame=target_frame,
        ).components
        return (new_point, new_orientation)


def _test():
    p = Pose3D(
        components=(
            VectorR3(
                data=(
                    0,
                    0,
                    0,
                ),
            ),
            Quaternion(
                data=(
                    0,
                    0,
                    0,
                    1,
                ),
            ),
        )
    )
    s = p.model_dump_json(indent=4)
    p2 = Pose3D.model_validate_json(s)
    print(p2.model_dump_json(indent=4))


if __name__ == "__main__":
    _test()
