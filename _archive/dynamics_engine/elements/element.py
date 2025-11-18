"""
Defines the model element base class from which all model elements will inheret.
"""
from __future__ import annotations

# Standard package imports
from typing import TYPE_CHECKING, Union

# Local package imports
if TYPE_CHECKING:
    from dynamics_engine.model import Model

__all__ = ['Element']

class Element:
    """
    Args:
        name (str): Name of element
        model (Union[None, Model]): Model to which the element will be registered in the
            instantiator if provided.  Otherwise, registration can be done explicitly after
            initialization.
    
    Attributes:
        name (str): [Element][dynamics_engine.elements.Element] name
        full_name (str): [Element][dynamics_engine.elements.Element] full name 
            (uses ADAMS naming convention .<model name>.<element name>)
        model (Model): [Model][dynamics_engine.model.Model] to which this [Element][dynamics_engine.elements.Element] is registered if registered
            (None if not registered)
    """
    def __init__(
            self, 
            name: str,
            model: Union[None, Model] = None,
        ) -> None:
        self._name = name
        self._model = None

        if model is not None:
            self.register_to_model(model)

    @property
    def name(self):
        return self._name
    
    @property
    def full_name(self):
        return self.model.full_name + '.' + self.name
    
    @property
    def model(self) -> Union[None, Model]:
        return self._model
    
    def register_to_model(self, model: Model):
        """
        Registers [Element][dynamics_engine.elements.Element] instance to [Model][dynamics_engine.model.Model] instance.
        Sets the stored model attribute to reference the model to which this has been registered.

        Args:
            model (Model): [Model][dynamics_engine.model.Model] instance to which this [Element][dynamics_engine.elements.Element] will be registered.
        
        Returns:
            (Self): returns a refernence to this element instance
        """
        self._model = model
        model.register_element(self)
        return self
    