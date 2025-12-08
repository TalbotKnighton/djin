from __future__ import annotations
from enum import StrEnum, auto
import functools
from typing import Any, Callable, Optional, Self, TypeVar, cast
import warnings
import typing_extensions

import numpy as np
from djin.containers.core import ID, Container, Stowable, Warehouse, get_warehouse
from djin.frames.core import Frame
from djin.math_objects.framed import Transformable3D, Point3D
from djin.math_objects.frameless import Tensor3x3Symmetric
from djin.math_objects.framed import (
    to_parent_frame,
    to_ground_frame,
    to_target_frame,
)
from djin.base import immutable

import pydantic as pyd


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

    def with_given_integral_convention(
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


C = tuple[Frame, InertiaTensor]


@immutable
class MassProperties(Transformable3D[C], Stowable):
    """"""

    mass: float
    center_of_mass: Frame
    inertia_tensor: InertiaTensor

    def get_components(self):
        return (
            self.center_of_mass,
            self.inertia_tensor,
        )

    def get_components_in_parent_frame(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        new_cm = starting_frame.contents.to_parent_frame(warehouse=warehouse)
        f = starting_frame.contents
        x, y, z = starting_frame.contents.pose.position.vector.data
        parallel_axis_term_in_new_frame = self.mass * np.array(
            [
                [(y**2 + z**2), -x * y, -x * z],
                [-y * x, (x**2 + z**2), -y * z],
                [-z * x, -z * y, (x**2 + y**2)],
            ]
        )

        r = f.pose.orientation.quaternion.as_rotation()
        inertia_tensor_rotated_to_new_frame = (
            r.as_matrix() @ self.inertia_tensor.array @ r.inv().as_matrix()
        )

        new_inertia_tensor = InertiaTensor.from_components(
            array=parallel_axis_term_in_new_frame + inertia_tensor_rotated_to_new_frame,
            integral_convention=self.inertia_tensor.integral_convention,
        )

        return (
            new_cm,
            new_inertia_tensor,
        )

    def get_components_in_target_frame(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ):
        frame = starting_frame.contents.to_target_frame(
            target_frame=target_frame,
            warehouse=warehouse,
        )
        return self.get_components_in_parent_frame(
            starting_frame=Container(id=-1, contents=frame),
            warehouse=warehouse,
        )

    def to_parent_frame(
        self,
        warehouse: Optional[Warehouse] = None,
    ):
        return to_parent_frame(
            transformable=self,
            starting_frame=self.center_of_mass.container_id,
            warehouse=warehouse,
        )

    def to_ground_frame(
        self,
        warehouse: Optional[Warehouse] = None,
    ):
        return to_ground_frame(
            transformable=self,
            starting_frame=self.center_of_mass.container_id,
            warehouse=warehouse,
        )

    def to_target_frame(
        self,
        target_frame: Optional[ID | Container[Frame]],
        warehouse: Optional[Warehouse] = None,
    ):
        return to_target_frame(
            transformable=self,
            starting_frame=self.center_of_mass.container_id,
            target_frame=target_frame,
            warehouse=warehouse,
        )
