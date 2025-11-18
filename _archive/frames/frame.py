"""
Defines the [Frame][frames.frame.Frame] class to be used for recursive frame transformations.
"""

from __future__ import annotations

# Standard package imports
from copy import deepcopy
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from djin.registry import CanRegister, Registry, default_registry

Number = float | int
from typing import Optional, Union, ClassVar

# Local package imports
from djin.frames.math_objects import EuclideanVector, Pose, Rotation
from djin.type_annotations import Array1D

__all__ = [
    "GROUND_FRAME",
    "GroundFrameSentinel",
    "Point3D",
    "Frame",
    "DirectionVector",
]


class GroundFrameSentinel(CanRegister):
    """
    Defines the GroundFrameSentinel properties.

    The GroundFrameSentinel is used as a global reference for all frames and is used to break
    recursive frame transformations.

    Attributes:
        pose (ClassVar[Pose]): Null pose
        parent (ClassVar[None]): No parent frame
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str = "GROUND_FRAME"
    registry: Registry = Field(default_registry, exclude=True)
    # pose: Pose = Pose.null()
    # parent: None = None

    @property
    def pose(self):
        return Pose.null()

    @property
    def parent(self):
        return None

    def change_parent_frame(
        self,
        new_frame: Optional[GroundFrameSentinel | Frame] = None,
    ):
        """
        It is not possible to change the parent frame of the GROUND_FRAME since it is `None`.
        But, this method is included for continuity with the [Frame][frames.frame.Frame] class
        so as to avoid errors if one attempts to call that method on a mixed collection of objects.

        Returns:
            (GroundFrameSentinel): Reference to ground frame sentinel.
        """
        return self


GROUND_FRAME = GroundFrameSentinel()


class Frame(CanRegister):
    """
    Frame pose.rotation is the active rotation of the frame.

    This is also the rotation matrix that converts vectors expressed in this frame to their expression in the parent frame

    That is, for [v]_Self, self.pose.rotation.as_matrix() @ v gives [v]_parent

    Attributes:
        parent (Union[GroundFrameSentinel, Frame]): Parent frame in which the
            [Pose][frames.math_objects.Pose] is expressed.
        pose (Pose): position and orientation of the [Frame][frames.frame.Frame] relative to `parent`.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pose: Pose
    parent: GroundFrameSentinel | Frame
    registry: Registry = Field(None, exclude=True)

    def set_pose_to_match_given_frame(self, frame: Frame | GroundFrameSentinel):
        """
        Updates `self.pose` to match the that of the given `frame`.

        Update is done in-place.

        The existing `parent` frame of this instance is preserved.  That is,
        the provided `frame` pose will be first transformed into the `self.parent` frame.

        Args:
            frame (Frame|GroundFrameSentinel): frame whose pose is to be matched
        """
        self.pose = frame.change_parent_frame(self.parent).pose

    def set_pose_in_ground_frame(self, pose: Pose):
        """
        Calls the [set_pose_to_match_given_frame][frames.frame.Frame.set_pose_to_match_given_frame]
        method assuming that the pose was given in the [GROUND_FRAME][frames.frame.GROUND_FRAME]
        """
        return self.set_pose_to_match_given_frame(Frame(pose=pose, parent=GROUND_FRAME))

    @property
    def _constructor(self):
        """
        This is the constructor to use for creating new copies.
        """
        return type(self)

    @classmethod
    def from_components(
        cls,
        position: EuclideanVector,
        rotation: Rotation,
        parent: GroundFrameSentinel | Frame,
    ) -> Frame:
        """
        Creates a new [Frame][frames.frame.Frame] from position and rotation components

        Args:
            position (Vector3D): Position relative to `parent`
            rotation (Rotation): Rotation relative to `parent`
            parent (GroundFrameSentinel|Frame): parent frame

        Returns:
            (Frame): New [Frame][frames.frame.Frame] instance
        """
        return cls(pose=Pose(position=position, rotation=rotation), parent=parent)

    def in_grandparent_frame(self):
        """
        Returns a copy in the parent's parent frame (grandparent frame).

        Returns:
            (Frame): returns a copy in the grandparent frame.
        """
        if self.parent == GROUND_FRAME:
            return deepcopy(self)
        else:
            position_in_grandparent_frame = EuclideanVector.from_array(
                self.parent.pose.position.as_array()
                + self.parent.pose.rotation.as_matrix() @ self.pose.position.as_array()
            )
            rotation_in_grandparent_frame = (
                self.parent.pose.rotation * self.pose.rotation
            )
            new_pose = Pose(
                position=position_in_grandparent_frame,
                rotation=rotation_in_grandparent_frame,
            )
            grandparent = self.parent.parent
            return self._constructor(pose=new_pose, parent=grandparent)

    def in_global_frame(self) -> Frame:
        """
        Returns copy expressed in global frame.
        Position in global frame is calculated recursively based on the parent frame, grandparent frame, etc.

        Returns:
            (Frame): copy expressed in global frame.
        """
        if self.parent == GROUND_FRAME:
            return deepcopy(self)
        else:
            return self.in_grandparent_frame().in_global_frame()

    def __str__(self):
        """
        Returns a string representation of the frame.
        Includes recursive representations of all parent, grandparent, great grand..., etc. frames.
        """
        newline = "\n"
        return f"""
        Frame:
            {self.pose.position = }
            self.pose.rotation.as_matrix() = 
                {str(self.pose.rotation.as_matrix()).replace(newline, newline + '                ')}
            {self.parent = }
        """

    def change_parent_frame(self, new_frame: GroundFrameSentinel | Frame):
        """
        Returns a copy expressed relative to the given `new_frame`

        Args:
            new_frame (GroundFrameSentinel|Frame): Frame in which the new instance is
                to be expressed.  Recursive frame transformations will be performed
                in this calculation.

        Returns:
            (Frame): new instance of [Frame][frames.frame.Frame] expressed relative to
                `new_frame` as the new parent.
        """
        self_global = self.in_global_frame()
        if new_frame == GROUND_FRAME:
            return self_global
        other_global = new_frame.in_global_frame()
        relative_position = EuclideanVector.from_array(
            self_global.pose.position.as_array() - other_global.pose.position.as_array()
        )
        relative_rotation = other_global.pose.rotation.inv() * self_global.pose.rotation
        return self._constructor.from_components(
            position=relative_position, rotation=relative_rotation, parent=new_frame
        )

    def as_array(self, change_to_frame: Optional[GroundFrameSentinel | Frame] = None):
        """
        Returns:
            (Array1D): pose and velocity in global frame as array with the following components:
                `x, y, z, qx, qy, qz, qscalar, vx, vy, vz, wx, xy, xz`
        """
        frame = (
            self
            if change_to_frame is None
            else self.change_parent_frame(change_to_frame)
        )
        return frame.pose.as_array()


from typing import Optional, Union, Type, ClassVar
from pydantic import BaseModel, ConfigDict
import numpy as np

# For typing
Number = float | int


class Vector3D(BaseModel):
    """
    Mixin class providing common vector operations that work for both Point3D and DirectionVector.
    These operations don't depend on how the vector transforms between frames.

    Attributes:
        vector (Vector3D): vector information
        frame (Frame): Frame in which the vector is expressed
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    vector: EuclideanVector
    frame: Frame | GroundFrameSentinel

    @property
    def _constructor(self):
        """
        This is the constructor to use for creating new copies.
        """
        return type(self)

    def __neg__(self):
        """
        Negates the vector (reflects it through the origin of the reference `frame`)

        Returns:
            Negated vector (reflected through `frame` origin)
        """
        return self._constructor(vector=-self.vector, frame=self.frame)

    @classmethod
    def from_components(cls, x: float, y: float, z: float, frame: Frame):
        """
        Creates a new vector from the individual components
        relative to the given Frame instance.

        Args:
            x: x-component
            y: y-component
            z: z-component
            frame: parent Frame

        Return:
            New vector instance
        """
        return cls(
            vector=EuclideanVector(x=x, y=y, z=z),
            frame=frame,
        )

    def in_global_frame(self):
        """
        Returns a new copy that has been frame transformed into the
        GROUND_FRAME reference.

        Returns:
            New vector instance transformed to the ground frame.
        """
        return self.change_frame(new_frame=GROUND_FRAME)

    @classmethod
    def null(cls):
        """
        Returns a null vector.

        Returns:
            Null vector instance (zero vector) relative to the ground frame.
        """
        return cls(
            vector=EuclideanVector.null(),
            frame=GROUND_FRAME,
        )

    def as_array(self, change_to_frame: Optional[Frame] = None) -> Array1D:
        """
        Returns the position components of the vector as an array.
        Optionally first transforms to a new parent frame `change_to_frame` first.

        Args:
            change_to_frame: Optional frame to which the
                vector will be transformed. If this argument is `None`, no transformation
                will be done and the xyz components will be returned as-is.

        Returns:
            Length 3 numpy array of xyz components in referenced to `change_to_frame`.
        """
        obj = (
            self.change_frame(new_frame=change_to_frame)
            if change_to_frame is not None
            else self
        )
        return obj.vector.as_array()

    def __add__(self, other: Vector3D):
        """
        Adds another vector to this vector.

        Args:
            other: vector to add to this vector.

        Returns:
            New vector instance with the sum.
        """
        assert isinstance(other, Vector3D)
        return self._constructor(
            vector=self.vector + other.change_frame(self.frame).vector,
            frame=self.frame,
        )

    def __radd__(self, other):
        """
        Adds this vector to another vector.

        Args:
            other: vector to add this vector to.

        Returns:
            New vector instance with the sum.
        """
        assert isinstance(other, Vector3D)
        return self._constructor(
            vector=other.vector + self.change_frame(other.frame).vector,
            frame=other.frame,
        )

    def __sub__(self, other):
        """
        Subtracts another vector from this vector.

        Args:
            other: vector to subtract from this vector.

        Returns:
            New vector instance with the difference.
        """
        assert isinstance(other, Vector3D)
        return self._constructor(
            vector=self.vector - other.change_frame(self.frame).vector,
            frame=self.frame,
        )

    def __rsub__(self, other):
        """
        Subtracts this vector from another vector.

        Args:
            other: vector from which to subtract this vector.

        Returns:
            New vector instance with the difference.
        """
        assert isinstance(other, Vector3D)
        return self._constructor(
            vector=other.vector - self.change_frame(other.frame).vector,
            frame=other.frame,
        )

    def __mul__(self, other: float):
        """
        Multiplies the vector by a scalar.

        Args:
            other: scalar to multiply the vector by.

        Returns:
            New vector instance with the result.
        """
        assert isinstance(other, (int, float))
        # Ensure that the other operand is a scalar (int or float)
        # before performing the multiplication.
        return self._constructor(vector=self.vector * other, frame=self.frame)

    def __rmul__(self, other: float):
        """
        Multiplies the vector by a scalar.

        Args:
            other: scalar to multiply the vector by.

        Returns:
            New vector instance with the result.
        """
        assert isinstance(other, (int, float))
        return self._constructor(vector=other * self.vector, frame=self.frame)

    def __truediv__(self, other: float):
        """
        Divides the vector by a scalar.

        Args:
            other: scalar to divide the vector by.

        Returns:
            New vector instance with the result.
        """
        assert isinstance(other, (int, float))
        return self._constructor(vector=self.vector / other, frame=self.frame)

    def change_frame(self, new_frame: Optional[Frame]) -> Vector3D:
        """
        Returns a new copy that has been frame transformed into the `new_frame` reference.

        Args:
            new_frame: New parent frame to which the current frame information
                will be transformed. If None, no transformation is done.

        Returns:
            New vector instance transformed to a new parent.
        """
        raise NotImplementedError("Must be implemented in subclasses.")
        # This is an abstract method that should be implemented in subclasses
        # to provide the specific frame transformation logic.
        # The method is not implemented here to enforce that subclasses provide their own implementation.
        # The `FramedVectorMixin` class is intended to be a mixin class that provides
        # common functionality for both `Point3D` and `DirectionVector` classes.


class Point3D(Vector3D):
    """
    Point3D stores a Vector3D and Frame such that the point vector can be
    frame transformed to a new parent frame.

    The point vector frame transformation scales direction and magnitude such that the physical
    endpoint is maintained when the vector tail is placed on the new parent Frame.

    Attributes:
        vector (Vector3D): vector information
        frame (Frame): Frame in which the vector is expressed
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    vector: EuclideanVector
    frame: Frame | GroundFrameSentinel

    def get_new_frame_at_point(
        self,
        rotation: Optional[Rotation] = None,
    ) -> Frame:
        """
        Returns a new frame at the point of the vector.
        The new frame is expressed in the same parent frame as the point vector.
        The new frame is rotated to match the parent frame of the frame in which
        the point vector is expressed.
        """
        return Frame.from_components(
            position=self.vector,
            rotation=rotation or self.frame.pose.rotation,
            parent=self.frame.parent,
        )

    def change_frame(self, new_frame: Optional[Frame]) -> "Point3D":
        """
        Returns a new copy that has been frame transformed into the `new_frame` reference.

        The point vector frame transformation scales direction and magnitude such that the physical
        endpoint is maintained when the vector tail is placed on the new parent Frame.

        Args:
            new_frame: New parent frame to which the current frame information
                will be transformed.

        Returns:
            New vector instance transformed to a new parent.
        """
        if new_frame is None:
            return self

        f = self.frame.change_parent_frame(new_frame)
        a = f.pose.position.as_array()
        b = f.pose.rotation.as_matrix() @ self.vector.as_array()
        c = a + b  # vector resolved into new_frame

        _constructor = type(self)
        return _constructor(
            vector=EuclideanVector.from_array(c),
            frame=new_frame,
        )


class DirectionVector(Vector3D):
    """
    DirectionVector stores a Vector3D and Frame such that the vector can be
    frame transformed to a new parent frame.

    The frame transformation amounts to a rotation to maintain physical direction and
    magnitude when expressed in a new parent Frame.

    Attributes:
        vector (Vector3D): vector information
        frame (Frame): Frame in which the vector is expressed
    """

    def change_frame(self, new_frame: Optional[Frame]) -> DirectionVector:
        """
        The frame transformation amounts to a rotation to maintain physical direction and
        magnitude when expressed in a new parent Frame.

        Args:
            new_frame: New parent frame to which the current frame information
                will be transformed. If None, no transformation is done.

        Returns:
            New vector instance transformed to a new parent.
        """
        if new_frame is None:
            return self

        f = self.frame.change_parent_frame(new_frame)
        b = f.pose.rotation.as_matrix() @ self.vector.as_array()

        _constructor = type(self)
        return _constructor(
            vector=EuclideanVector.from_array(b),
            frame=new_frame,
        )


if __name__ == "__main__":
    import numpy as np

    f1 = Frame.from_components(
        position=EuclideanVector(x=0, y=0, z=0),
        rotation=Rotation.from_rotvec((0, np.pi / 2, 0)),
        parent=GROUND_FRAME,
    )
    f2 = Frame.from_components(
        position=EuclideanVector(x=0, y=0, z=0),
        rotation=Rotation.from_rotvec((np.pi / 2, 0, 0)),
        parent=f1,
    )
    # print(f2.in_grandparent_frame())
    # print(f2.in_global_frame())

    print(f2)
    print(f2.change_parent_frame(f1))
    print(GROUND_FRAME)
    GROUND_FRAME.pose = Pose.null()
    print(
        Frame(
            pose=Pose.null(),
            parent=GROUND_FRAME,
        )
    )
    print(
        DirectionVector(
            vector=EuclideanVector(
                x=1,
                y=2,
                z=3,
            ),
            frame=f2,
        ).change_frame(GROUND_FRAME)
    )
