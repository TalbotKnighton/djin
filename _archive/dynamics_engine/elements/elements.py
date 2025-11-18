"""
Defines a custom registry for [Element][dynamics_engine.elements.Element] instances.
"""
from __future__ import annotations

# Standard package imports
from typing import Union

# Local package imports
from djin.dynamics_engine.elements.element import Element
from djin.dynamics_engine.registry import Registry
from djin.type_annotations import Self

__all__ = ['Elements']

class Elements(Registry):
    """
    Custom regiistry for generic `Elements`.

    Args:
        elements (Union[list[Element], Elements, None]): Optionally provide 
            a list of elements to pre-populate registry or a pre-existing registry 
            whose elements references to copy into a new registry.
    """
    def __init__(self, elements: Union[list[Element], Elements, None]=None):
        if elements is None:
            self._elements: list[Element] =  []
        elif isinstance(elements, Elements):
            self._elements: list[Element] = elements._elements
        else:
            self._elements: list[Element] = elements
    
    def register_element(self, element: Element) -> Self:
        """
        Registers a reference to provided [Element][dynamics_engine.elements.Element] into this registry.

        Args:
            element (Element): The element whose reference is to be registered

        Returns:
            (Self): reference to this registry instance.
        """
        try:
            used_names = [e.name for e in self._elements]
            assert element.full_name not in used_names
        except AssertionError:
            raise ValueError(
                f'\n\n\tNaming conflict for {element.full_name = }.'  
                f'\n\t\tUse unique names for dynamic elements.'
            )
        self._elements.append(element)
        return self
