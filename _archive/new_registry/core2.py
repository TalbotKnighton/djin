from __future__ import annotations
from pathlib import Path
from typing import ClassVar, Optional, Self
import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    computed_field,
    field_validator,
    model_validator,
)

IDType = str | int


def _get_registry_type_key(obj: type | str):
    if hasattr(obj, "get_registry_type_key"):
        return obj.get_registry_type_key()
    if not isinstance(obj, (str, bytes)):
        return obj.__name__
    return str(obj)


class Registry(BaseModel):
    """ """

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=False)

    # Attributes
    elements: dict[IDType, dict[IDType, SerializeAsAny[Registrant]]] = {}

    def get_object(self, t: type, i: IDType):
        """Get an object from the registry by its ID."""
        t = _get_registry_type_key(t)
        try:
            return self.elements[t].get(i, None)
        except KeyError:
            raise ValueError(f"Object not found: type {t=}, id {i=}")

    def add_object(
        self,
        obj: Registrant,
        allow_overwrite: bool = False,
    ):
        """Add an object to the registry."""
        t = _get_registry_type_key(obj)

        if t not in self.elements:
            self.elements[t] = {}

        elements_t = self.elements[t]
        if allow_overwrite or (obj.name not in elements_t):
            elements_t.update({obj.name: obj})

        return obj

    def remove_object(self, t: type, name: IDType):
        """Remove an object from the registry."""
        t = _get_registry_type_key(t)
        del self.types[t].instances[name]
        return self


class Registrant(BaseModel):
    """ """

    registry: ClassVar[Registry] = Registry()

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=False)

    # Attributes
    name: Optional[IDType] = None

    @computed_field
    def type(self) -> str:
        return self.__class__.__name__

    @classmethod
    def get_registry_type_key(cls):
        return cls.__name__

    def register(self, registry: Registry) -> Self:
        registry.add_object(self)

    @model_validator(mode="after")
    def register(self):
        self.registry.add_object(self)
        return self


class Reference(BaseModel):
    """ """

    registry: ClassVar = Registrant.registry

    type: str
    name: IDType

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        if not isinstance(v, str):
            return v.__name__
        return v

    def get_object(self):
        return self.registry.get_object(
            type=self.type,
            i=self.name,
        )

    def remove_object(self):
        return self.registry.remove_object(
            type=self.type,
            name=self.name,
        )


# class RegistryFramework(BaseModel):
#     """ """

#     model_config = ConfigDict(arbitrary_types_allowed=False)
#     registries: dict[IDType, Registry] = {
#         DEFAULT_REGISTRY_NAME: Registry(name=DEFAULT_REGISTRY_NAME)
#     }

#     def get_registry(self, name: str) -> Registry:
#         """Register a new registry."""
#         if name not in self.registries:
#             raise ValueError(f"Registry {name} does not exist.")
#         return self.registries.get(name=name)

#     def add_registry(self, name: str) -> Self:
#         """Register a new registry."""
#         if name not in self.registries:
#             self.registries[name] = Registry(name=name)
#         return self.registries[name]

#     def remove_registry(self, name: str) -> Self:
#         """Delete a registry."""
#         if name in self.registries:
#             del self.registries[name]
#         return self


class MyClassA(Registrant):
    b: Reference


class MyClassB(Registrant):
    a: Reference


a = MyClassA(
    name="a",
    b=Reference(
        type=MyClassB,
        name="b",
    ),
)

b = MyClassB(
    name="b",
    a=Reference(
        type=MyClassA,
        name="b",
    ),
)


def load_registry() -> Registry:
    return Registry(name="test")


print(a.model_dump_json(indent=4))
print(b.model_dump_json(indent=4))
print(registries.model_dump_json(indent=4))
