"""
Defines the base class for a DynamicElement.  
[DynamicElement][dynamics_engine.elements.dynamic_elements.dynamic_element.DynamicElement]s must include state vector and state derivative information 
for use in a system state function.
"""
from __future__ import annotations

# Standard package imports
from abc import ABC, abstractmethod
from typing import Union

# Local package imports
from djin.dynamics_engine.elements.element import Element
from djin.type_annotations import Array1D
from djin.type_annotations.self_type import Self

__all__ = ['DynamicElement']


class DynamicElement(Element, ABC):
    """
    [DynamicElement][dynamics_engine.elements.dynamic_elements.dynamic_element.DynamicElement] serves as an interface class to define what methods are
    required to be implemented for anything that contributes to the model state funciton
    """

    @abstractmethod
    def get_state_vector_length(self) -> int:
        """
        Returns:
            (int): Length of state vector for each instance of this element.
                It is envisioned that the length will be a constant 
                and not calculated based on the actual state vector.
        """
    
    @abstractmethod
    def get_state_vector(self) -> Array1D:
        """
        Should be written to return the state vector.
        
        - The state vector will be a function of the internally stored memory defined in child classes.
        - The state vector derivative will be a function of internally stored memory.
        
        Example:
            See the `RigidBody3D` class.

        Returns:
            (Array1D): State vector
        """

    @abstractmethod
    def get_state_vector_time_derivative(self) -> Array1D:
        """
        Should be written to return the time derivative of the state vector.
        
        - The length should be identical to the state vector with a component-wise correspondence.
        - The state vector time derivative will be a function of internally stored memory.
        
        Example:
            See the `RigidBody3D` class.

        Returns:
            (Array1D): time derivative of state vector.
        """
    
    @abstractmethod
    def set_state(self, state_vector: Array1D, **kwargs) -> Self:
        """
        Should be written to ingests a 1D state vector and 
        update internal memory states accordingly.

        Args:
            state_vector (Array1D): 1D array of state elements

        Returns:
            (Self): Reference to this instance of [DynamicElement][dynamics_engine.elements.dynamic_elements.dynamic_element.DynamicElement] (allowing use as decoration)
        """

    def consume_from_system_state_vector(self, system_state_vector: Array1D) -> Union[None, Array1D]:
        """
        Consumes `N` elements from the total system state vector and returns the remaining elements.

        `N` is determined by the `get_state_vector_length` method.

        Args:
            system_state_vector (Array1D): total state vector from which the elements for this
                for setting the state of this object will be consumed.
        
        Returns:
            (Array1D): Remaining state array (unconsumed elements) to be used for setting other object states. 
                Returns None if no unconsumed elements remain.
        """
        self.set_state(state_vector=system_state_vector[:self.get_state_vector_length()])
        if len(system_state_vector) > self.get_state_vector_length():
            return system_state_vector[self.get_state_vector_length():]
        else:
            return None