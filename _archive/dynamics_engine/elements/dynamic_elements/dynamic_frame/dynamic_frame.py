"""
Defines a [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] which adds name and velocity to static `Frame` parent class.
"""

from __future__ import annotations

# Standard package imports
from dataclasses import dataclass, field

from djin.frames.frame import GroundFrameSentinel

Number = float | int
import numpy as np
from typing import Optional, Union

# Related package imports
from djin.frames import Frame, DirectionVector, EuclideanVector, GROUND_FRAME
from djin.type_annotations import Array1D

# Local package imports
from djin.dynamics_engine.snapshot_builder import (
    SnapshotBuilder,
    SnapshotGeneratingCallback,
)
from djin.dynamics_engine.output_naming_conventions import Filter, Component


__all__ = ["FrameVelocity", "DynamicFrame"]


@dataclass
class FrameVelocity:
    """
    Frame velocity

    Args:
        linear (ResolvedVector3D): linear velocity relative to or expressed (resolved)
            in a given reference frame
        linear (ResolvedVector3D): angular velocity relative to or expressed (resolved)
            in a given reference frame

    """

    linear: DirectionVector = field(default_factory=DirectionVector.null)
    angular: DirectionVector = field(default_factory=DirectionVector.null)

    @classmethod
    def null(cls) -> FrameVelocity:
        """
        Returns a null frame velocity (both linear and angular velocities zero)

        Returns:
            (FrameVelocity): A new instance of `FrameVelocity` with
                zero velocity relative to the global frame.
        """
        return cls()

    # def set_state(
    #         self,
    #         frame_velocity: FrameVelocity,
    #         keep_reference_frame: bool = True,
    #     ) -> Self:
    #     """
    #     Args:
    #         frame_velocity (FrameVelocity): Velocity to which this object should be updated
    #         keep_reference_frame (bool): If true, input velocity vectors will be transformed to existing
    #             reference frame.  Otherwise, the reference frame will be changed to match input
    #             `frame_velocity` object.

    #     Returns:
    #         (Self): this instance with updated velocity vectors (both linear and angular)
    #     """
    #     if keep_reference_frame:
    #         self.linear = frame_velocity.linear.change_frame(new_frame=self.linear.frame)
    #         self.angular = frame_velocity.angular.change_frame(new_frame=self.angular.frame)
    #     else:
    #         self.linear = frame_velocity.linear
    #         self.angular = frame_velocity.angular
    #     return self

    def copy_with_updated_reference_frames(
        self,
        reference_frame_linear: Frame,
        reference_frame_angular: Frame,
    ) -> Frame:
        """
        Frame transforms the stored velocity vectors to match the input reference frames.

        Args:
            reference_frame_linear (Frame): Frame to which linear rate is referenced
            reference_frame_angular (Frame): Frame to which angular rate is referenced

        Returns:
            (FrameVelocity): New instance with updated velocity vectors
        """
        return type(self)(
            linear=self.linear.change_frame(new_frame=reference_frame_linear),
            angular=self.angular.change_frame(new_frame=reference_frame_angular),
        )

    def copy_with_updated_reference_frames_to_match_object(
        self,
        frame_velocity: FrameVelocity,
    ) -> FrameVelocity:
        """
        Frame transforms the stored velocity vectors to match the reference frames of the input object.

        Args:
            frame_velocity (FrameVelocity): FrameVelocity for which the linear and angular
                velocity vector reference frames should be copied

        Returns:
            (FrameVelocity): New instance with updated velocity vectors
        """
        return self.copy_with_updated_reference_frames(
            reference_frame_linear=frame_velocity.linear.frame,
            reference_frame_angular=frame_velocity.angular.frame,
        )

    @classmethod
    def from_components(
        cls,
        vx: Number,
        vy: Number,
        vz: Number,
        wx: Number,
        wy: Number,
        wz: Number,
        frame: Frame,
    ) -> FrameVelocity:
        """
        Returns a new `FrameVelocity` constructed from scalar component arguments.

        Args:
            vx (Number): Linear velocity, x-component
            vy (Number): Linear velocity, y-component
            vz (Number): Linear velocity, z-component
            wx (Number): Angular velocity, x-component
            wy (Number): Angular velocity, y-component
            wz (Number): Angular velocity, z-component
            frame (Frame): Reference frame in which the velocity components are defined.

        Returns:
            (FrameVelocity): new `FrameVelocity` instance constructed from scalar component arguments.
        """
        linear_velocity = DirectionVector(
            vector=EuclideanVector.from_array([vx, vy, vz]),
            frame=frame,
        )
        angular_velocity = DirectionVector(
            vector=EuclideanVector.from_array([wx, wy, wz]),
            frame=frame,
        )
        return cls(linear=linear_velocity, angular=angular_velocity)

    @classmethod
    def fixed_to_frame(cls, frame: Frame) -> FrameVelocity:
        """
        Returns a new instance of `FrameVelocity` that is null relative to given frame.
        That is, the velocity that would cause a [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] to be fixed to the given `frame`.

        Args:
            frame (Frame): The `Frame` instance to which the null velocity vectors are fixed.

        Returns:
            (FrameVelocity) A zero velocity with respect to the given `Frame` instance
        """
        linear_velocity = DirectionVector(
            vector=EuclideanVector.null(),
            frame=frame,
        )
        angular_velocity = DirectionVector(
            vector=EuclideanVector.null(),
            frame=frame,
        )
        return cls(linear=linear_velocity, angular=angular_velocity)

    @classmethod
    def from_array(
        cls,
        array: Array1D,
        frame: Frame,
    ) -> FrameVelocity:
        """
        Creates a new `FrameVelocity` instance from an array of components in a given reference `Frame`.

        Args:
            array (Array1D): Array of velocity components (vx, vy, vz, wx, wy, wz) a the given `frame`.
            frame (Frame): The frame in which the array of velocity components is expressed.

        Returns:
            (FrameVelocity): a new `FrameVelocity` instance from an array of components in a given reference `Frame`.
        """
        assert len(array) == 6
        return cls.from_components(*tuple(array), frame=frame)

    def change_to_frame(self, frame: Frame):
        """
        Returns a new instance of `FrameVelocity` in the desired frame.

        Args:
            frame (Frame): Frame in which newly created `FrameVelocity` components will be expressed.

        Returns:
            (FrameVelocity): New `FrameVelocity` object expressed in desired `frame`
        """
        constructor = type(self)
        return constructor.from_array(
            array=self.as_array(change_to_frame=frame),
            frame=frame,
        )

    def as_array(
        self, change_to_frame: Optional[Frame | GroundFrameSentinel] = None
    ) -> Array1D:
        """
        Concatenates the linear and angular velocity array representations to create a combined
        1D array.

        Args:
            change_to_frame (Optional[Frame|GroundFrameSentinel]): Frame in which the velocities
                are to be resolved.  Option to leave default value of `None` such that the
                velocities output in the frame in which they are already defined.
                A common usage would be to output velocities in the global frame
                for dynamics calculations.

        Returns:
            (Array1D): Returns the linear and angular velocity array representations concatenated
                into a single 1D vector.
        """
        return np.concatenate(
            [
                self.linear.as_array(change_to_frame),
                self.angular.as_array(change_to_frame),
            ]
        )


@dataclass
class DynamicFrame(Frame):
    """
    Adds several features (such as velocity) to the parent `Frame` class for use in dynamics equations.

    Args:
        velocity (Union[FrameVelocity, None]): Stores the velocity of the [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame].  Allows
            frame transformations of the velocities (See
            [dynamics_engine.elements.dynamic_elements.dynamic_frame.FrameVelocity.as_array][]
            and `).
            If no velocity is specified, the default behavior is to be kinematically
            fixed in the `parent` reference frame (via `FrameVelocity.fixed_to_frame(frame=self.parent)`).
        name (Union[str, None]): Optional name for the [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] instance.  A name must be
            provided before the memory snapshot request methods can be used.
            This is because the [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] name is used to name the outputs.
    """

    velocity: Union[FrameVelocity, None] = None
    name: Union[str, None] = None

    def __post_init__(self):
        """
        Sets `self.velocity = FrameVelocity.fixed_to_frame(frame=self.parent)` if provided velocity
        at instantiation is `None`.
        """
        if self.velocity is None:
            self.velocity = FrameVelocity.fixed_to_frame(frame=self.parent)

    def set_velocity(
        self,
        velocity: FrameVelocity,
        use_new_velocity_reference_frames: bool = False,
    ):
        """
        Sets the [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] velocity.
        The reference frame for the [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] will be preserved by converting
        the given `FrameVelocity` to the existing reference frame unless
        `use_new_velocity_reference_frames` is `True`.

        Note that is is possible to set different reference frames for linear and angular velocity.
        That might be useful for implementing a sherical bushing attached to
        a translational joint since the spherical busing rotates with one body but its location is fixed to another.

        Args:
            velocity (FrameVelocity): velocity to which the [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] will be updated.
                The reference frame for the [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] will be preserved by converting
                the given `FrameVelocity` to the existing reference frame unless
                new reference frames are specifically given.
            use_new_velocity_reference_frames (bool): If `False` (default), then
                the provided velocities will be converted to the existing reference frame.
                That is the the frame velocity reference frame will not be changed.
                If `True`, the velocity reference frames will be updated to whatever
                is provided as the reference frames to the resolved linear and angular velocity vectors
                in the `FrameVelocity` instance passed to the `velocity` argument.
        """
        if use_new_velocity_reference_frames:
            self.velocity.linear = velocity.linear
            self.velocity.angular = velocity.angular
        else:
            self.velocity.linear = velocity.linear.change_frame(
                self.velocity.linear.frame
            )
            self.velocity.angular = velocity.angular.change_frame(
                self.velocity.angular.frame
            )
        return self

    def as_array(self, change_to_frame: Optional[Frame | GroundFrameSentinel] = None):
        """
        Args:
            change_to_frame (Optional[Frame | GroundFrameSentinel]): optionally request array representation in a given frame.

        Returns:
            (Array1D): pose and velocity in parent frame (or `change_to_frame` if given)
                as array with the following components:
                `x, y, z, qx, qy, qz, qscalar, vx, vy, vz, wx, xy, xz`
        """
        pose_array = super().as_array(change_to_frame=change_to_frame)
        velocity_array = self.velocity.as_array(change_to_frame=change_to_frame)
        return np.concatenate([pose_array, velocity_array])

    def _get_pose_snapshot(self) -> SnapshotGeneratingCallback:
        """
        A [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] pose `Snapshot` generator.

        Returns:
            (SnapshotGeneratingCallback): Returns a snapshot generating callback function
                to be registered to a snapshot generator.
        """
        from dynamics_engine.output_naming_conventions import Filter, Component

        def pose_snapshot():
            """
            This is a function that returns the pose object of this Dynamic Frame.
            """
            name = self.name
            try:
                assert name is not None
            except AssertionError:
                raise ValueError(
                    "You requested an output for an un-named DynamicFrame.  You must name a DynamicFrame to be able to request its output."
                )
            names = [str(Filter.frame(name).component(e.name)) for e in Component]
            frame = self.in_global_frame()
            return {name: value for name, value in zip(names, frame.pose.as_array())}

        return pose_snapshot

    def request_global_pose(self, snapshot_builder: SnapshotBuilder):
        """
        Registers the global pose snapshot generating callback to the `snapshot_builder`.

        Args:
            snapshot_builder (SnapshotBuilder): Snapshot building function.

        Returns:
            (Self): Returns this instance to be used as a decorator in a chain of commands.
        """
        snapshot_builder.register_snapshot_generating_callback(
            self._get_pose_snapshot()
        )
        return self
