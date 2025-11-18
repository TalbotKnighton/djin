"""
Defines a `DynamicElements` custom `Registry` which inherits from the `Elements` custom `Registry`.
"""
from __future__ import annotations

# Standard package imports
Number = float|int
import numpy as np

# Local package imports
from djin.dynamics_engine.elements.elements import Elements
from djin.dynamics_engine.elements.dynamic_elements.dynamic_element import DynamicElement
from djin.type_annotations import Array1D


__all__ = ['DynamicElements']

class DynamicElements(Elements):
    """
    Custom registry for dynamic elements.

    Has methods for collectively dealing with the list of registered dynamic elements.
    """

    @property
    def _dynamic_elements(self) -> list[DynamicElement]:
        return self._elements
    
    def set_state_vector(self, system_state_vector: Array1D) -> None:
        """
        Sets the state of each individual registered element by sequentially consuming
        states from the total system state vector.

        Args:
            system_state_vector (Array1D): Total system state vector
        
        Returns:
            (None): nothing
        """
        remaining_elements = system_state_vector
        for e in self._dynamic_elements:
            remaining_elements = e.consume_from_system_state_vector(remaining_elements)

    def get_state_vector(self) -> Array1D:
        """
        Concatenates the state vectors from all registered elements into a 
        total system state vector

        Returns:
            (Array1D): System state vector (numpy array)
        """
        return np.concatenate([e.get_state_vector() for e in self._dynamic_elements])
    
    def get_state_derivative_vector(self) -> Array1D:
        """
        Concatenates the time derivative of the state vectors 
        from all registered elements into a 
        time derivative of the total system state vector

        Returns:
            (Array1D): Time derivative of system state vector (numpy array)
        """
        return np.concatenate([e.get_state_vector_time_derivative() for e in self._dynamic_elements])
    
    def system_dynamics_function(self, time: Number, system_state_vector: Array1D) -> Array1D:
        """
        This is the dynamics function to numerically integrate.

        The function performs the following sequention actions:
        
        - update the elements states from the total system state vector
        - return new state derivative calculated based on the updated system state

        Args:
            time (Number): simulation time
            system_state_vector (Array1D): system state vector.  
                Integrator will pass in calculated latest predicted state vector here 
                causing the system elements to update their internal stored memory 
                and calculate corresponding derivative.
        """
        self.set_state_vector(system_state_vector=system_state_vector)
        return self.get_state_derivative_vector()
        
