"""
Defines a generalized load vector
"""

from __future__ import annotations

# Standard package imports
import numpy as np
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union, Callable, Type

# Local package imports
from djin.dynamics_engine.elements.element import Element
from djin.frames import DirectionVector, EuclideanVector, GROUND_FRAME
from djin.frames.frame import GroundFrameSentinel

if TYPE_CHECKING:
    from djin.dynamics_engine.elements.dynamic_elements.rigid_body import RigidBody6DOF
    from djin.dynamics_engine.elements.dynamic_elements.dynamic_frame.dynamic_frame import (
        Frame,
    )
    from djin.type_annotations import Length6Iterable, Array1D, Self

__all__ = ["GeneralizedLoadVector", "NullaryGeneralizedLoadCallback", "GeneralizedLoad"]


@dataclass
class GeneralizedLoadVector:
    """
    Stores linear and angular loads

    Args:
        linear (ResolvedVector3D): force vector in a given frame
        angular (ResolvedVector3D): torque vector in a given frame
    """

    linear: DirectionVector
    angular: DirectionVector

    def __neg__(self) -> GeneralizedLoadVector:
        """
        Returns:
            (GeneralizedLoadVector): New instance of `GeneralizedLoadVector` having the force and torque vectors negated.
        """
        return type(self)(linear=-self.linear, angular=-self.angular)

    @classmethod
    def from_array(
        cls,
        generalized_force_array: Length6Iterable,
        frame: Frame,
    ) -> GeneralizedLoadVector:
        """
        Args:
            generalized_force_array (Length6Iterable): An array of force and moment components fx, fy, fz, mx, my, mz
            frame (Frame): The frame in which the force and moment components are expressed

        Returns:
            (GeneralizedLoadVector): New instance of `GeneralizedLoadVector` built from the provided components in the given `frame`
        """
        linear = DirectionVector(
            vector=EuclideanVector.from_array(generalized_force_array[:3]),
            frame=frame,
        )
        angular = DirectionVector(
            vector=EuclideanVector.from_array(generalized_force_array[3:]),
            frame=frame,
        )
        return cls(
            linear=linear,
            angular=angular,
        )

    def as_array(
        self,
        change_to_frame: Optional[Frame | GroundFrameSentinel] = None,
    ) -> Array1D:
        """
        Args:
            change_to_frame (Optional[Frame | GroundFrameSentinel]): Optional `Frame` to which the
                forces and torques should be converted before returning the length 6 array representation.

        Return:
            (Array1D): A length 6 numpy array having force and torque components in the
                frame in which the force and torque are already expressed (default) or
                in the `change_to_frame` (if provided).
        """
        self_in_desired_frame = (
            self.change_frame(new_frame=change_to_frame)
            if change_to_frame is not None
            else self
        )
        return np.concatenate(
            [
                self_in_desired_frame.linear.as_array(),
                self_in_desired_frame.angular.as_array(),
            ]
        )

    def change_frame(
        self,
        new_frame: Optional[Frame | GroundFrameSentinel],
    ) -> GeneralizedLoadVector:
        """
        Args:
            new_frame (Optional[Frame | GroundFrameSentinel]): Frame to which the force and torque are to be expressed.
                If `new_frame == None` a n, the identity transformation will be used (no change to the components).

        Returns:
            (GeneralizedLoadVector): New instance of `GeneralizedLoadVector` expressed in `new_frame`.
        """
        _constructor = type(self)
        force = self.linear.change_frame(new_frame=new_frame)
        r = self.linear.frame.change_parent_frame(
            new_frame=new_frame
        ).pose.position.as_array()
        torque = DirectionVector(
            vector=EuclideanVector.from_array(
                self.angular.as_array(change_to_frame=new_frame)
                + np.cross(r, force.as_array())
            ),
            frame=self.angular.frame,
        )
        return _constructor(
            linear=force,
            angular=torque,
        )


NullaryGeneralizedLoadCallback = Callable[[], GeneralizedLoadVector]
"""
A nullary function is one that takes no arguments.

A `NullaryGeneralizedLoadCallback` takes no arguments and returns an instance of `GeneralizedLoadVector`
"""


@dataclass
class GeneralizedLoad(Element):
    """
    The `GeneralizedLoad` class uses an argument-less ('nullary') callback to
    compute a generalized load vector.

    To create the `NullaryGeneralizedLoadCallback`, use either

    - A callable class (has __call__ defined) instance that references any required model elements or model states.
    - A function that is defined using references to any required model elements or model states.

    Args:
        name (str): Name of the `GeneralizedLoad` object
        action_body (RigidBody3D): Body on which the action generalized load (as returned by `load_function_callback`) is to be applied.
        load_function_callback (NullaryGeneralizedLoadCallback): An argument-less function that returns
            a GeneralizedLoadVector (force and torque resolved into particular frame(s)).
        reaction_body (Union[None, RigidBody3D]): Body on which the equal and opposite generalized load is to be applied.
            The reaction load will be applied to the same positions as the action load in order to presereve angular momentum.
            A point-to-point force is achieved by causing the force to always adjust direction so as
            always to be applied along the line between two points.
            If `reaction_body == None`, then only the action force will be applied causing the total system
            energy and momentum to change (commonly used for external forcing functions or for thrusters).
    """

    def __init__(
        self,
        name: str,
        action_body: RigidBody6DOF,
        load_function_callback: NullaryGeneralizedLoadCallback,
        reaction_body: Union[None, RigidBody6DOF] = None,
    ) -> None:
        super().__init__(name=name, model=getattr(reaction_body, "model", None))
        self._action_body = action_body
        self._reaction_body = reaction_body
        self._load_function_callback = load_function_callback
        self.register_to_bodies(action_body=action_body, reaction_body=reaction_body)

    def register_to_bodies(
        self,
        action_body: RigidBody6DOF,
        reaction_body: Union[None, RigidBody6DOF],
    ) -> Type[Self]:
        """
        Registers this instance of `GeneralizedLoad` to the provided `RigidBody3D` instances.

        This provides the action and reaction bodies with a reference to this `GeneralizedLoad` instance
        such that the bodies will call for the evaluated load during their dynamics calculations.

        Args:
            action_body (RigidBody3D): body on which
                the action force (as returned by the `load_function_callback`) will be applied
            reaction_body (Union[None, RigidBody3D]): body on which the reaction force will be applied

        Returns:
            (Type[Self]): Returns this instance of `GeneralizedLoad` so that the method can be used
                as a chained decorator.
        """
        action_body.register_load_function_callback(self._load_function_callback)
        if reaction_body is not None:
            reaction_body.register_load_function_callback(
                lambda: -self._load_function_callback()
            )
        return self
