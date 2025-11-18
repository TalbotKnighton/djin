"""
Defines a 6DOF rigid body
"""

from __future__ import annotations

# Standard package imports
import numpy as np
from typing import Union, TYPE_CHECKING

# Local package imports
from djin.dynamics_engine.elements.dynamic_elements.dynamic_element import (
    DynamicElement,
)
from djin.dynamics_engine.elements.dynamic_elements.dynamic_frame.dynamic_frame import (
    DynamicFrame,
    FrameVelocity,
    DirectionVector,
)
from djin.frames import (
    EuclideanVector,
    Rotation,
    Pose,
    Quaternion,
    GROUND_FRAME,
    Frame,
)
from djin.frames.frame import GroundFrameSentinel
from djin.mass_properties import MassProperties
from djin.type_annotations import Self, Array1D

if TYPE_CHECKING:
    from djin.dynamics_engine.model import Model
    from djin.dynamics_engine.elements.loads.load import NullaryGeneralizedLoadCallback
    from djin.dynamics_engine.snapshot_builder import Snapshot, SnapshotBuilder

__all__ = ["RigidBody6DOF"]


class RigidBody6DOF(DynamicElement):
    """
    The `RigidBody6DOF` child of [DynamicElement][dynamics_engine.elements.dynamic_elements.dynamic_element.DynamicElement] can be registered to a [Model][dynamics_engine.model.Model] to include
    6DOF dynamics.  Multiple instances can be registered to the same model and made to interact
    via load classes such `GeneralizedLoad`.

    Args:
        name (str): Name of the body
        mass_properties (MassProperties): Rigid body mass properties (CoM, CoM pose, and inertia tensor in CoM frame)
        initial_velocity (FrameVelocity): Velocity of the CoM frame.
        model (Model): If provided, causes the `RigidBody6DOF` to be implicitly registered to the given [Model][dynamics_engine.model.Model] instance
            during `RigidBody6DOF` instantiation.

    Attributes:
        name (str): Name of the body
        mass_properties (MassProperties): Rigid body mass properties (CoM, CoM pose, and inertia tensor in CoM frame)
        model (Model): If provided, causes the `RigidBody6DOF` to be implicitly registered to the given [Model][dynamics_engine.model.Model] instance
            during `RigidBody6DOF` instantiation.
        cm_frame (DyanmicFrame): [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame]
            body-fixed at the `RigidBody6DOF` CoM
            and to which the inertia tensor is referenced.
    """

    def __init__(
        self,
        name: str,
        mass_properties: MassProperties,
        initial_velocity: FrameVelocity = FrameVelocity,
        model: Model = None,
    ):
        super().__init__(name=name, model=model)
        self._load_function_callbacks: list[NullaryGeneralizedLoadCallback] = []
        # Set the _cm frame and mass properties
        self._cm_frame: DynamicFrame = DynamicFrame(
            parent=GROUND_FRAME,
            pose=Pose.null(),
            name="cm",
            velocity=initial_velocity,
        )
        self._mass_properties = mass_properties
        self._sync_cm_frame_to_mass_properties(mass_properties=self._mass_properties)

    def _sync_cm_frame_to_mass_properties(
        self,
        mass_properties: Union[None, MassProperties],
    ) -> Self:
        """
        Changes `MassProperties` object to reference self.cm_frame using the `MassProperties.change_to_frame` method.

        This effectively changes the `mass_properties` instance from referencing a static `Frame`
        in which the CoM position was given to one referencing to a [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] at the CoM.

        Args:
            mass_properties (MassProperties): `MassProperties` instance according to which
                the `cm_frame` position and parent frame should be updated

        Returns:
            (Self): returns an instance to self such that
                this can be used as a chain decorator if needed.
        """
        if isinstance(mass_properties, MassProperties):
            self.cm_frame.parent = mass_properties.frame
            self.cm_frame.pose = Pose(
                position=EuclideanVector.from_array(
                    mass_properties.center_of_mass.position.as_array()
                ),
                rotation=Rotation.null(),
            )
            self._mass_properties = mass_properties.change_frame(self.cm_frame)
        return self

    def register_load_function_callback(
        self,
        callback_function: NullaryGeneralizedLoadCallback,
    ) -> Self:
        """
        Registers a generalized load function callback to be used in dynamics calculations

        Args:
            callback_function (NullaryGeneralizedLoadCallback): Callback to be evaluated and summed
                (along with other callbacks) to find total force and moment components in dynamics
                calculations.

        Returns:
            (Self): To be used as a chained decorator method.
        """
        self._load_function_callbacks.append(callback_function)
        return self

    @property
    def cm_frame(self) -> DynamicFrame:
        return self._cm_frame

    @property
    def mass_properties(self):
        return self._mass_properties

    @mass_properties.setter
    def mass_properties(self, mass_props: MassProperties):
        """
        Sets internally stored mass properties and updates `self.cm_frame`

        Args:
            mass_props (MassProperties): New mass properties for the body.
        """
        self._mass_properties = mass_props
        self._sync_cm_frame_to_mass_properties(mass_properties=mass_props)

    def get_state_vector_length(self) -> int:
        """
        Returns the state vector length for a 6DOF rigid body.
        In this particular formation, the state vector has 13 components.

        See `DynamicsEngine.get_state_vector` for a list of the components.
        """
        return 13

    def get_state_vector(self) -> Array1D:
        """
        Returns the state vector for a 6DOF rigid body using a quaternion formulation for the orientation.

        Returns:
            (Array1D): 1d Array having the values `x, y, z, qx, qy, qz, qscalar, vx, vy, vz, wx, wy, wz`
        """
        return self.cm_frame.as_array()

    def get_angular_momentum_about_cm_in_global_frame(self) -> Snapshot:
        """
        Computes the angular momentum about the CoM in the global frame
        and returns the components as a `Snapshot`

        Returns:
            (Snapshot): A dictionary or `Snapshot` of angular momentum component values corresponding to standardized keys.
        """
        from dynamics_engine.output_naming_conventions import Filter, Component

        I = self.mass_properties.in_global_frame().inertia_tensor.tensor
        omega = self.cm_frame.velocity.angular.in_global_frame().as_array()
        L = I @ omega
        return {
            str(
                Filter.body(name=self.name)
                + Filter.angular_momentum(component=Component.x)
            ): L[0],
            str(
                Filter.body(name=self.name)
                + Filter.angular_momentum(component=Component.y)
            ): L[1],
            str(
                Filter.body(name=self.name)
                + Filter.angular_momentum(component=Component.z)
            ): L[2],
        }

    def request_angular_momentum_about_cm_in_global_frame(
        self,
        snapshot_builder: SnapshotBuilder,
    ):
        """
        Requests that the angular momentum about the CoM in the global frame
        be output by the snapshot_builder.

        Args:
            snapshot_builder (SnapshotBuilder): Snapshot builder to which the angular momentum
                snapshot generator callback function should be registered.

        Returns:
            (Self): To be used as a chained decorator method if desired.
        """
        snapshot_builder.register_snapshot_generating_callback(
            callback=self.get_angular_momentum_about_cm_in_global_frame
        )
        return self

    def get_state_vector_time_derivative(self) -> Array1D:
        """
        Computes the state vector time derivative via 6DOF dynamics equations
        (uses quaternion math)
        and returns it.

        Returns:
            (Array1D): Numpy array giving the time derivative of the state vector evaluated
                as prescribed in this function.
        """
        # calculate multi-use quantities once for efficiency
        cm_rotation = self.cm_frame.in_global_frame().pose.rotation

        mass = self.mass_properties.center_of_mass.mass

        # Velocity
        # Linear
        velocity_linear = (
            self.cm_frame.velocity.linear.in_global_frame().vector.as_array()
        )
        # Angular (for quaternion): https://arxiv.org/pdf/0811.2889
        velocity_angular = (
            self.cm_frame.velocity.angular.in_global_frame().vector.as_pure_quat()
        )
        qdot: Quaternion = (
            0.5 * velocity_angular * Quaternion.from_array(cm_rotation.as_quat())
        )
        qdot = qdot.as_array()

        # Acceleration
        evaluated_loads_in_ground_frame = np.atleast_2d(
            [
                # callback().as_array(change_to_frame=self.cm_frame)
                callback().as_array(change_to_frame=GROUND_FRAME)
                for callback in self._load_function_callbacks
            ]
        )
        generalized_load_vector = np.sum(evaluated_loads_in_ground_frame, axis=0)
        if len(generalized_load_vector) == 0:
            generalized_load_vector = np.zeros(6)
        # print(generalized_load_vector)
        # Linear
        # F = dp/dt = dm/dt v + m dv/dt
        # accel = m^-1 * (F - v*dm/dt)
        mass_term = 0  # assuming constant mass for now
        force_term = generalized_load_vector[:3]
        accel_linear = (force_term - mass_term) / mass

        # Angular
        # T = dL/dt = dI_g/dt w + I_g alpha
        # alpha = I_g^-1 @ (T - \dot{I_g} @ w)
        # I_g = R I_b R^T
        # \dot{I}_g = \dot{R} I_b R^T + R I_b \dot{R^T} + R \dot{I_b} R^T
        # \dot{I_b} = 0 (for rigid body of fixed mass distribution)
        # \dot{I}_g = \dot{R} I_b R^T + R I_b \dot{R}^T
        # R = [e1 e2 e3]
        # \dot{e} = w_skew @ e
        # \dot{R} = [w_skew@e1 w_skew@e2 w_skew@e3]
        # \dot{R} = w_skew @ R
        # \dot{I}_g = w_skew (R I_b R^T) + R I_b (w_skew R)^T
        # \dot{I}_g = w_skew @ I_g + R I_b R^T w_skew^T
        # w_skew^T = - w_skew
        # w_skew @ v = w cross v
        # w_skew = [[0, -wz, wy], [wz, 0, -wx], [-wy, wx, 0]]
        # \dot{I}_g = w_skew @ I_g - R I_b R^T w_skew^T
        # \dot{I}_g = w_skew @ I_g - I_g @ w_skew
        # \dot{I}_g @ w = w_skew @ I_g @ w - I_w @ w_skew @ w
        # w_skew @ w = w cross w = \vec{0}
        # \dot{I}_g @ w = w cross I_g @ w
        inertia = self.mass_properties.in_global_frame().inertia_tensor
        inertia_term = np.cross(
            velocity_angular.vector.as_array(),
            inertia.tensor @ velocity_angular.vector.as_array(),
        )
        torque_term = generalized_load_vector[3:]
        accel_angular = inertia.tensor_inverse @ (torque_term - inertia_term)
        return np.concatenate(
            [
                velocity_linear,
                qdot,
                accel_linear,
                accel_angular,
            ]
        )

    def set_state(
        self,
        state_vector: Array1D,
        state_vector_parent_frame: Frame | GroundFrameSentinel = GROUND_FRAME,
    ) -> Self:
        """
        Sets the internal `RigidBody6DOF` state based on the provided `state_vector`.

        Args:
            state_vector (Array1D): state vector from which the internal state of this object
                should be set.  This method is called by the numerical solver to update
                the object state in order to be able to calculate the next state vector time derivative.

        Returns:
            (Self): Returns this instance of `RigidBody6DOF` for use as a decorator chain method if desired.
        """
        # Unpack state vector
        x, y, z, qx, qy, qz, qscalar, vx, vy, vz, wx, wy, wz = tuple(state_vector)
        # Set cm_frame pose
        self.cm_frame.pose = Pose(
            position=EuclideanVector.from_array([x, y, z]),
            rotation=Rotation.from_quat([qx, qy, qz, qscalar]),
        ).change_to_frame(
            to_frame=self.cm_frame.parent, from_frame=state_vector_parent_frame
        )
        # Set cm_frame velocity
        self.cm_frame.velocity = FrameVelocity.from_components(
            vx=vx,
            vy=vy,
            vz=vz,
            wx=wx,
            wy=wy,
            wz=wz,
            frame=state_vector_parent_frame,
        ).copy_with_updated_reference_frames_to_match_object(self.cm_frame.velocity)
