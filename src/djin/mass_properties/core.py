from __future__ import annotations
from enum import StrEnum, auto
import functools
from typing import Any, Callable, Optional, Self, TypeVar, cast
import warnings
import typing_extensions

import numpy as np
from djin.containers.core import Container, Stowable, Warehouse, get_warehouse
from djin.frames.core import Frame
from djin.math_objects.framed import Transformable3D, Point3D
from djin.math_objects.frameless import Tensor3x3Symmetric
from djin.base import immutable
import pydantic as pyd

T = TypeVar("T", bound=Callable[..., Any])


def not_implemented(alternate_method: str) -> Callable[[T], T]:
    """Mark a method as not implemented and suggest an alternative.

    Args:
        alternate_method: Name of the method to use instead

    Returns:
        Decorator that marks the method as not implemented
    """

    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__qualname__} is not implemented. Use {alternate_method} instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            raise NotImplementedError(f"Use {alternate_method} instead")

        return cast(T, wrapper)

    return decorator


class IntegralConvention(StrEnum):
    positive = auto()
    negative = auto()


@immutable
class InertiaTensor(Tensor3x3Symmetric):
    integral_convention: IntegralConvention

    @property
    def array(self) -> np.ndarray:
        a = self.array
        c = -1 if self.integral_convention == IntegralConvention.positive else 1
        for i, j in zip((0, 1, 2), (0, 1, 2)):
            if i != j:
                a[i, j] = c * a[i, j]
        return a

    @classmethod
    @typing_extensions.deprecated("Use InertiaTensor.from_components instead")
    def from_array(cls, array: np.ndarray) -> Self:
        raise NotImplementedError(f"Use {cls.from_components.__qualname__} instead")

    @classmethod
    def from_components(
        cls,
        array: np.ndarray,
        integral_convention: IntegralConvention,
    ) -> InertiaTensor:
        """"""
        return cls(
            xx=array[0, 0],
            yy=array[1, 1],
            zz=array[2, 2],
            xy=array[0, 1],
            zx=array[2, 0],
            yz=array[1, 2],
            integral_convention=integral_convention,
        )

    def with_integral_convention(
        self,
        integral_convention: IntegralConvention,
    ) -> InertiaTensor:
        c = 1 if integral_convention == self.integral_convention else -1
        a = self.array
        for i, j in zip((0, 1, 2), (0, 1, 2)):
            if i != j:
                a[i, j] = c * a[i, j]
        return type(self).from_components(
            array=a,
            integral_convention=integral_convention,
        )


C = tuple[Point3D, InertiaTensor]


@immutable
class MassProperties(Transformable3D[C], Stowable):
    """"""

    mass: float

    @property
    def center_of_mass(self) -> Point3D:
        return self.components[0]

    @property
    def inertia_tensor(self) -> InertiaTensor:
        return self.components[1]

    def _to_parent_frame_components(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> C:
        new_cm = self.center_of_mass.to_parent_frame(starting_frame=starting_frame)
        frame = starting_frame.contents
        f_pos = frame.pose.position.components.array
        x, y, z = tuple(f_pos)
        parallel_axis_term_in_new_frame = self.mass * np.array(  # calculated in
            [
                [(y**2 + z**2), -x * y, -x * z],
                [-y * x, (x**2 + z**2), -y * z],
                [-z * x, -z * y, (x**2 + y**2)],
            ]
        )

        inertia_tensor_rotated_to_new_frame = (
            frame.pose.orientation.components.as_rotation().as_matrix()
            @ self.inertia_tensor.array
        )

        new_inertia_tensor = InertiaTensor.from_components(
            array=parallel_axis_term_in_new_frame + inertia_tensor_rotated_to_new_frame,
            integral_convention=self.inertia_tensor.integral_convention,
        )

        return (
            new_cm,
            new_inertia_tensor,
        )

    def _to_target_frame_components(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> C:
        frame = starting_frame.contents.to_target_frame(
            starting_frame=starting_frame,
            target_frame=target_frame,
            warehouse=warehouse,
        )
        return self._to_parent_frame_components(
            starting_frame=Container(id=-1, contents=frame),
            warehouse=warehouse,
        )
