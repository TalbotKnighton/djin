from __future__ import annotations

from importlib import import_module
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
    ValidationError,
)

IDType = str | int

OBJECT_REGISTRY = "object_registry"


def _get_registry_type_key(obj: type | str):
    if hasattr(obj, "get_registry_type_key"):
        return obj.get_registry_type_key()
    if not isinstance(obj, (str, bytes)):
        return obj.__name__
    return str(obj)


class BaseComponent(BaseModel):
    """ """

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

    def register(self, registry: Registry | ByTypeRegistry) -> Self:
        registry.add_object(self)


class Registry(BaseComponent):
    """ """

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=False)

    # Attributes
    instances: dict[IDType, SerializeAsAny[BaseComponent]] = Field({}, exclude=False)

    def get_next_unused_id(self) -> IDType:
        """Get the next unused ID"""
        return np.max([i for i in self.instances if isinstance(i, int)]) + 1

    def get_object(self, name: IDType):
        """Get an object from the registry by its ID."""
        if name in self.instances:
            return self.instances.get(name)
        raise ValueError(f"Object with ID {name} does not exist.")

    def add_object(self, obj: BaseComponent, allow_overwrite=True):
        """Add an object to the registry."""
        if not allow_overwrite and (obj.name in self.instances):
            raise ValueError(
                f"Object with name {obj.name = } already exists in {type(self).__name__} for {self.name}."
            )
        self.instances[obj.name] = obj
        return obj

    def remove_object(self, name: str):
        """Remove an object from the registry."""
        del self.instances[name]
        return self


class ByTypeRegistry(BaseComponent):
    """ """

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=False)

    # Attributes
    types: dict[IDType, SerializeAsAny[Registry]] = Field({}, exclude=False)

    def get_object(self, t: type, name: IDType):
        """Get an object from the registry by its ID."""
        t = _get_registry_type_key(t)
        try:
            return self.types[t].get_object(name)
        except KeyError:
            raise ValueError(f"Object with ID {name} does not exist.")

    def add_object(
        self,
        obj: BaseComponent,
        allow_overwrite: bool = False,
    ):
        """Add an object to the registry."""
        t = _get_registry_type_key(obj)

        if t not in self.types:
            self.types[t] = Registry(name=t)

        self.types[t].add_object(
            obj,
            allow_overwrite=allow_overwrite,
        )

        return obj

    def remove_object(self, t: type, name: IDType):
        """Remove an object from the registry."""
        t = _get_registry_type_key(t)
        del self.types[t].instances[name]
        return self


class ByTypeRegistries(BaseModel):
    """ """

    registries: dict[str, ByTypeRegistry] = {
        OBJECT_REGISTRY: ByTypeRegistry(
            name=OBJECT_REGISTRY,
        ),
    }

    def get_next_unused_id(self) -> IDType:
        """Get the next unused ID"""
        return np.max([i for i in self.registries if isinstance(i, int)]) + 1

    def get_registry(self, name: IDType):
        """Get an object from the registry by its ID."""
        if name in self.registries:
            return self.registries.get(name)
        raise ValueError(f"Registry with ID {name} does not exist.")

    def add_registry(self, registry: ByTypeRegistry, allow_overwrite=True):
        """Add an object to the registry."""
        if not allow_overwrite and (registry.name in self.registries):
            raise ValueError(f"Registry with ID {registry.name} already exists.")
        self.registries[registry.name] = registry
        return registry

    def remove_registry(self, name: str):
        """Remove an object from the registry."""
        del self.registries[name]
        return self

    def load_registry(
        self,
        path: Path,
        allow_overwrite: bool = False,
    ):
        btr = ByTypeRegistry.model_validate_json(
            path.read_text(),
        )
        self.add_registry(
            btr,
            allow_overwrite=allow_overwrite,
        )
        return btr


registries = ByTypeRegistries()


class ByTypeComponent(BaseComponent):
    """ """

    @model_validator(mode="after")
    def register(self):
        registries.get_registry(OBJECT_REGISTRY).add_object(self)
        return self


class ByTypeReference(BaseModel):
    """ """

    type: str
    name: IDType

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        if not isinstance(v, str):
            return v.__name__
        return v

    def get_object(self):
        return registries.get_registry(
            name=OBJECT_REGISTRY,
        ).get_object(
            type=self.type,
            name=self.name,
        )

    def remove_object(self):
        return registries.get_registry(
            name=OBJECT_REGISTRY,
        ).remove_object(
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


class TypeSpec(BaseModel):
    module_spec: str
    method_spec: str

    @field_validator("module_spec", mode="before")
    @classmethod
    def validate_module_spec(cls, module_spec: str | Path):
        if isinstance(module_spec, Path):
            module_spec = str(module_spec.resolve())
        if not isinstance(module_spec, str):
            raise ValidationError(
                f"Module spec should be given as a string or a Path. Given {module_spec = }"
            )
        return module_spec

    @field_validator("method_spec", mode="after")
    @classmethod
    def validate_method_spec(cls, method_spec: str):
        if len(method_spec.split(".")) > 2:
            raise ValidationError(
                f"Method spec should have no more than 1 `.` in it {method_spec = }"
            )
        return method_spec

    @classmethod
    def from_string(cls, spec: str):
        module_spec, method_spec = tuple(spec.split(":"))
        return cls(
            module_spec=module_spec,
            method_spec=method_spec,
        )

    @classmethod
    def from_obj(cls, obj: object) -> Self:
        module_spec, method_spec = tuple(obj.__class__.__name__.split("."))
        return cls(
            module_spec=module_spec,
            method_spec=method_spec,
        )

    @property
    def constructor(self):
        obj = import_module(self.module_spec)
        if "." in self.method_spec:
            class_spec, method_spec = self.method_spec.split(".")
            obj = getattr(obj, class_spec)
            obj = getattr(obj, method_spec)
        else:
            obj = getattr(obj, self.method_spec)
        return obj


class MyClassA(ByTypeComponent):
    b: ByTypeReference


class MyClassB(ByTypeComponent):
    a: ByTypeReference


a = MyClassA(
    name="a",
    b=ByTypeReference(
        type=MyClassB,
        name="b",
    ),
)

b = MyClassB(
    name="b",
    a=ByTypeReference(
        type=MyClassA,
        name="b",
    ),
)


# print(a.model_dump_json(indent=4))
# print(b.model_dump_json(indent=4))
print(registries.model_dump_json(indent=4))
