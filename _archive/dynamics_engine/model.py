"""
Defines a Model class used to define and solve the dynamic equations for arbitrary systems.
"""

from __future__ import annotations

# Standard package imports
import numpy as np

# Local package imports
from djin.dynamics_engine.elements.dynamic_elements.dynamic_elements import (
    DynamicElement,
    DynamicElements,
)
from djin.dynamics_engine.elements.element import Element
from djin.dynamics_engine.explicit_solver import ExplicitSolution, ExplicitSolverMethods
from djin.dynamics_engine.snapshot_builder import (
    SnapshotBuilder,
    SnapshotGeneratingCallback,
)
from djin.type_annotations import Array1D

__all__ = ["Model"]


class Model:
    """
    Defines a dynamic model to solve.  'Solving' the dynamic system consists of
    numerically integrating the system dynamic equations to probagate the state vector
    forward or backwards in time.

    Registered model elements are used to contrsuct the total state vector / state derivative vector.

    A memory snapshot function is evaluated at user-specified time intervals to save as a
    text file for post-processing.

    Args:
        name (str): Name of the model.

    Attributes:
        name (str): Name of the model.
        full_name (str): Full name of the model using ADAMS naming convention (.<name>)
        snapshot_builder (SnapshotBuilder):  Callback function to be evaluated at specified time intervales
            to produce desired model outputs.
        dynamic_elements (DynamicElements): A
            customized iterable containing all registered dynamic elements.
            `dynamic_elements` is looped over to creat the state and state derivative vectors.
    """

    def __init__(self, name: str = "model"):
        self._name = name
        self._dynamic_elements = DynamicElements()
        self._snapshot_builder = SnapshotBuilder()

    @property
    def snapshot_builder(self) -> SnapshotBuilder:
        """
        Returns:
            (SnapshotBuilder): Callback function to be evaluated at specified time intervales
                to produce desired model outputs.
        """
        return self._snapshot_builder

    def register_snapshot_generating_callback(
        self,
        callback: SnapshotGeneratingCallback,
    ) -> SnapshotBuilder:
        """
        Registers a zero-argument callback function to be evaluated at output time steps.

        Args:
            callback (SnapshotCallback): Callback function to be evalutted at output time steps

        Returns:
            (SnapshotBuilder): Returns the instance of SnapshotBuilder to which the callback was registered.
        """
        return self.snapshot_builder.register_snapshot_generating_callback(
            callback=callback,
        )

    @property
    def dynamic_elements(self) -> DynamicElements:
        """
        Returns:
            (DynamicElement): Iterable container of registered dynamic elements.
                Returns a copy of the dynamic elements registry to prevent users
                from manually editing the list without using the intented registry API.
        """
        return DynamicElements(self._dynamic_elements)

    @property
    def name(self):
        """
        Returns:
            (str): Name of the model
        """
        return self._name

    @property
    def full_name(self):
        """
        Returns:
            (str): Full name of the model (Uses ADAMS naming convention .<name>)
        """
        return "." + self.name

    def register_element(self, element: Element):
        """
        Registers an [Element][dynamics_engine.elements.Element] to the appropriate registry.

        [DynamicElement][dynamics_engine.elements.dynamic_elements.dynamic_element.DynamicElement] instances will be registered to the `dynamic_elements` registry.

        Other Elements are presently ignored.

        Args:
            element (Element): Any type of element to be registered to the apropriate model registry.

        Returns:
            (any): Registry to which the element was rigistered or None if element was not handled.
        """
        if isinstance(element, DynamicElement):
            return self._dynamic_elements.register_element(element)
        if isinstance(element, Element):
            pass  # TODO: should I do something for generic elements?
        else:
            raise ValueError(f"object type `{type(element) = }` is not recognized")

    def solve_ivp(
        self,
        output_times: Array1D,
        method: ExplicitSolverMethods = ExplicitSolverMethods.rk45,
        output_monitor=True,
    ):
        """
        Runs an explicit numerical integration of the dynamic system state.

        Args:
            output_times (Array1D): A 1D array of times at which memory snapshots should be evaluated for output.
            method (ExplicitSolverMethods): Specifies the solver method to be used for numerical integration.
                Defaults to Runge-Kutta 4-5 solution (via scipy.integrate.solve_ivp interface).
            output_monitor (bool): Wether or not to output progress to terminal.

        Returns:
            (ExplicitSolution): Explicit solution of model dynamic equations.
        """
        return ExplicitSolution.solve_ivp(
            model=self,
            output_times=output_times,
            method=method,
            snapshot_builder=self._snapshot_builder,
            output_monitor=output_monitor,
        )


if __name__ == "__main__":
    """
    An example dynamics model is created and run.
    """
    # imports
    import djin.frames as fr
    import djin.mass_properties as mp
    import djin.dynamics_engine as de

    # Model
    model = de.Model()

    # Mass properties
    cm_position = fr.EuclideanVector.null()
    cm_rotation = fr.Rotation.null()
    cm_frame = de.DynamicFrame(
        parent=fr.GROUND_FRAME,
        pose=fr.Pose(
            position=cm_position,
            rotation=cm_rotation,
        ),
    )
    center_of_mass = mp.CenterOfMass(
        mass=1,
        position=fr.Point3D(
            vector=cm_position,
            frame=cm_frame,
        ),
    )
    inertia_tensor = mp.InertiaTensor(
        i_xx=1,
        i_yy=2,
        i_zz=2.999,
        i_xy=0,
        i_yz=0,
        i_zx=0,
        sign_convention=mp.ProductsOfInertiaSignConvention.positive_integrals,
    )
    mass_props = mp.MassProperties(
        center_of_mass=center_of_mass,
        inertia_tensor=inertia_tensor,
    )

    # Initial velocity
    initial_velocity_linear = fr.DirectionVector(
        vector=fr.EuclideanVector(0, 0, 0),
        frame=fr.GROUND_FRAME,
    )
    initial_velocity_angular = fr.DirectionVector(
        vector=fr.EuclideanVector(0.001, 1, 0),
        frame=fr.GROUND_FRAME,
    )
    initial_velocity = de.FrameVelocity(
        linear=initial_velocity_linear,
        angular=initial_velocity_angular,
    )

    # Body
    body = de.RigidBody6DOF(
        "body",
        mass_properties=mass_props,
        initial_velocity=initial_velocity,
        model=model,
    )

    # Loads
    # load = de.Load(
    #     name='load',
    #     action_body=body,
    #     load_function_callback=lambda : de.GeneralizedLoadVector.from_array(
    #         generalized_force_array=[0, 0, 0, 0, 0, 0],
    #         frame=body.cm_frame,
    #     ),
    # )
    # f2 = de.DynamicFrame(
    #     parent=body.cm_frame,
    #     pose=fr.Pose(
    #         position=fr.Vector3D(1, 0, 0),
    #         rotation=fr.Rotation.null(),
    #     ),
    #     name='output_frame',
    # )
    # f2.request_global_pose(model._snapshot_builder)

    # Request outputs
    body.cm_frame.name = "cm"
    body.cm_frame.request_global_pose(model.snapshot_builder)
    body.request_angular_momentum_about_cm_in_global_frame(model.snapshot_builder)

    # Run model
    solution = model.solve_ivp(
        output_times=np.linspace(0, 10, 1000),
        method=ExplicitSolverMethods.rk45,
    )

    # Post process data
    from dynamics_engine.output_naming_conventions import Filter

    print(solution.memory_dataframe.filter(regex=str(Filter.angular_momentum())))
    import matplotlib.pyplot as plt

    euler313 = np.array(
        [
            fr.Rotation.from_quat(_[3 : 3 + 4]).as_euler("ZXZ", degrees=True)
            for _ in solution.states
        ]
    )

    rotations = [fr.Rotation.from_quat(_[3 : 3 + 4]) for _ in solution.states]

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    y = np.array([0, 1, 0])
    vecs = [r.as_matrix() @ y for r in rotations]
    x = [v[0] for v in vecs]
    y = [v[1] for v in vecs]
    z = [v[2] for v in vecs]
    ax.scatter(x, y, z)
    # plt.plot(solution.times, euler313[:, 0], '-.', label='0')
    # plt.plot(solution.times, euler313[:, 1], '-.', label='1')
    # # plt.plot(t, euler313[:, 2], '-.', label='2')
    # plt.legend()
    # # plt.scatter(t, euler313)
    plt.show()
    # print(sol.y[:,1])
    # print(body.cm_frame)
    # print(sol.y)
