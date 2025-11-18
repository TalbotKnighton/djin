from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, model_validator
from typing import Dict, Any, Optional, Set

__all__ = ["CanRegister", "Registry", "default_registry"]

"""
Can you write me a Registry class with a default_registry instance?  I will add an optional `registry` method to the Frame class that points to the default_frame_registry.  I can use that registry to print the frame.  The name of the frame will either be a string or an integer.  The registry should assign the next unused name if None is given.  I may add such functionality to other types in the future, so let's have the registry store the data on a per class method.  Probably we can use the class name as a key in a dictionary and then store a set of the used names which can be ints or strings
"""


class Registry(BaseModel):
    """
    A class to manage a registry of objects with unique keys.

    Attributes:
        registry (Dict[str, Any]): A dictionary to store the objects in the registry.
    """

    registry: Dict[str, Dict[int | str, SerializeAsAny[CanRegister]]] = Field(
        default_factory=dict
    )

    def add(self, obj: CanRegister) -> None:
        """
        Add an object to the registry.

        Args:
            obj (CanRegister): The unique key for the object.
            value (Any): The object to be added.
        """
        assert obj.name not in self.registry.get(obj.__class__.__name__, {}).keys()
        if obj.__class__.__name__ in self.registry.keys():
            subregistry = self.registry[obj.__class__.__name__]
            assert not obj.name in subregistry.keys()
            subregistry[obj.name] = obj
        else:
            self.registry[obj.__class__.__name__] = {obj.name: obj}

    def get(self, t: str | type, name: int | str) -> Optional[Any]:
        """
        Retrieve an object from the registry.

        Args:
            key (str): The unique key for the object.

        Returns:
            Optional[Any]: The object associated with the key, or None if not found.
        """
        t = getattr(t, "__name__", t)
        return self.registry.get(t, {}).get(name, None)

    # def remove(self, key: str | type) -> None:
    #     """
    #     Remove an object from the registry.

    #     Args:
    #         key (str): The unique key for the object.
    #     """
    #     key = key.__name__ if hasattr(key, "__name__") else key
    #     if key in self.registry:
    #         del self.registry[key]

    def get_next_unused_id(self, t: str | type) -> int:
        """
        Get the next unused ID for a new object.
        Returns:
            int: The next unused ID.
        """
        t = getattr(t, "__name__", t)
        if t not in self.registry.keys():
            return 0
        else:
            return max([i.name for i in self.registry.get(t)])


class CanRegister(BaseModel):
    """ """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: Optional[int | str] = None
    registry: Optional[Registry] = Field(None, exclude=True)

    # @model_validator(mode="after")
    # def register(self) -> CanRegister:
    #     """
    #     Register the object in the registry if it has a name.

    #     Returns:
    #         HasName: The instance itself.
    #     """
    #     if self.registry is not None:
    #         if self.name is None:
    #             self.name = self.registry.get_next_unused_id(t=type(self))
    #         else:
    #             self.registry.add(self)
    #     return self


default_registry = Registry()
