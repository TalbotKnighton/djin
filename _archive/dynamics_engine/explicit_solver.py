"""
Defines the explicit solver interface for solving model dynamic equations.

This is essentiallyl a convenient wrapper on scipy.integrate.solve_ivp such that
the results are returned in a convenient dataclass.
"""
from __future__ import annotations

# Standard package imports
from dataclasses import dataclass
from enum import StrEnum
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from typing import TYPE_CHECKING

# Local Package Imports
from djin.dynamics_engine.snapshot_builder import SnapshotBuilder, Snapshot
from djin.type_annotations import Array1D, Array2D
if TYPE_CHECKING:
    from djin.dynamics_engine.model import Model

__all__ = ['ExplicitSolverMethods', 'ExplicitSolution']

class ExplicitSolverMethods(StrEnum):
    """
    Enumeration of available explicit numerical integration schemes

    Attributes:
        rk45 (str): Runge-Kutta 4/5 integration method.
    """
    rk45 = 'RK45'
    dop853 = 'DOP853'

@dataclass
class ExplicitSolution:
    """
    A dataclass for holding data from a numerical integration.
    Use the [solve_ivp][dynamics_engine.explicit_solver.ExplicitSolution.solve_ivp] classmethod as an instantiator to generate the dataclass.

    Args:
        times (Array1D): Solution evaluation times.
        states (Array2D): 2D matrix giving the state array evalutated at each snapshot time.
            M[i, j] gives the jth element of the state vector at the ith time step.
        snapshots (list[Snapshot]): list of memory snapshots evaluated at each time step.
            The snapshot differs from the state vector in that it contains only user-specified outputs.
            These can be any arbitrary calculated quantities (generally based on time, state, and state derivative).
    
    Attributes:
        memory_dataframe (pd.DataFrame): A dataframe of memory snapshots versus time.
            Each row is an evaluated snapshot with time as the row index.
            Column headers are the named outputs.
    """
    times: Array1D
    states: Array2D
    snapshots: list[Snapshot]

    @property
    def memory_dataframe(self):
        """
        Memory snapshots as a 2D DataFrame.

        Returns:
            (pd.DataFrame): A dataframe of memory snapshots versus time.
                Each row is an evaluated snapshot with time as the row index.
                Column headers are the named outputs.
        """
        df = pd.DataFrame.from_records(self.snapshots)
        df.index = pd.Index(data=self.times, name='Time')
        return df
    
    @classmethod
    def solve_ivp(
            cls, 
            model: Model, 
            output_times: Array1D, 
            method: ExplicitSolverMethods = ExplicitSolverMethods.rk45,
            snapshot_builder: SnapshotBuilder = None,
            output_monitor=True,
        ):
        """
        Solvs the input [Model][dynamics_engine.model.Model] dynamic equations 
        using the specified provided `method`
        with `snapshot_builder` memory snapshots 
        evaluated at provided `output_times`.

        If `output_monitor` is `True`, solution progress will be printed to terminal in real time.

        Args:
            model (Model): Model whose dynamic equations are to be explicitlly solved
            output_times (Array1D): Times at which the desired outputs are to be evaluated
            method (ExplicitSolverMethods): Numerical method to use for solving the dynamic equations.
            snapshot_builder (SnapshotBuilder): Zero-argument callable returning a Snapshot
            output_monitor (bool): Whether or not to output solver progress to terminal
        
        Returns:
            (ExplicitSolution): Stored values from the explicit simulation of [Model][dynamics_engine.model.Model] dynamic equations.
                Values include evalutation times, state vector at evaluation times, memory snapshot at evaluation times.
        """
        snapshot_builder = snapshot_builder if snapshot_builder is not None else SnapshotBuilder()
        times = []
        state_arrays = []
        memory_snapshots = []
        
        n = len(output_times - 2)

        times.append(output_times[0])
        state_arrays.append(model.dynamic_elements.get_state_vector())
        memory_snapshots.append(snapshot_builder.get_snapshot())
        for i, (start, stop) in enumerate(zip(output_times[:-1], output_times[1:])):
            sol = solve_ivp(
                fun=model.dynamic_elements.system_dynamics_function,
                t_span=[start, stop],
                y0=model.dynamic_elements.get_state_vector(),
                method=method.value,
            )
            times.append(sol.t[-1])
            state_arrays.append(sol.y[:, -1])
            memory_snapshots.append(snapshot_builder.get_snapshot())
            cp = (i+2)/n*100
            if output_monitor:
                print(
                    f'Solution Completion Percentage {cp:.2f}%', 
                    end='\r' if cp != 100 else None, 
                    flush=cp!=100,
                )
        return cls(
            times = np.array(times), 
            states = np.array(state_arrays),
            snapshots = memory_snapshots,
        )

# if __name__ == '__main__':
#     df = pd.DataFrame.from_dict([{'a': 1, 'b': 2}, {'a': 1, 'b': 2}])
#     df.index = pd.Index(data=['a', 'b'], name='Time')
#     print(df)