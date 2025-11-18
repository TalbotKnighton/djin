from __future__ import annotations
from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    validate_call,
    model_validator,
)

from contextlib import contextmanager
from typing import Iterator, List, Type, Self
import contextvars
from typing import ClassVar, Self, TypeVar, Generic, Optional, cast, Any

# 1. Use Any for initial declaration, then properly type it later
# Use string for forward reference to Registry
current_registry: contextvars.ContextVar["Registry | None"]

__all__ = [
    "current_registry",
    "registry_context",
    "get_current_registry",
]


class Registrant(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=False)

    id: str

    _registry_type: ClassVar[str] = "Registrant"

    @computed_field
    def registry_type(self) -> str:
        return self._registry_type

    @model_validator(mode="after")
    def register(self) -> Self:
        self.register_to_current_registry()
        return self

    def register_to_current_registry(self) -> Self:
        # Use the declared variable, which will be properly initialized later
        if current_registry is not None:
            registry = current_registry.get()
            if registry is not None:
                registry.set_registrant(self)
        return self


T = TypeVar("T", bound=Registrant)


class Registry(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid", frozen=False)

    registrants: dict[str, T] = {}

    def get_registrant(self, name: str) -> T | None:
        return self.registrants.get(name, None)

    def set_registrant(self, registrant: T):
        if registrant.id in self.registrants:
            raise ValueError(
                f"Registrant with name '{registrant.id}' already exists."
            )
        self.registrants[registrant.id] = registrant


# 3. Now properly initialize with the correct type
# Use string literals for the type argument to avoid reference before definition
current_registry = contextvars.ContextVar[Registry | None](
    "current_registry",
    default=None,
)


@contextmanager
def registry_context(registry: Registry[T]) -> Iterator[Registry[T]]:
    """
    Context manager for setting the current registry.

    Args:
        registry: The registry to use within this context

    Yields:
        (Registry[T]): The registry that was set for the context
    """
    token = current_registry.set(registry)
    try:
        yield registry
    finally:
        current_registry.reset(token)


def get_current_registry(type: T) -> Optional[Registry[T]]:
    """
    Get the current registry from the context.

    Returns:
        The current registry or None if no registry is set
    """
    registry = current_registry.get()
    if registry is not None:
        if registry.
    return registry


class Reference(BaseModel, Generic[T]):
    model_config = ConfigDict(
        arbitrary_types_allowed=False,
        frozen=True,
    )
    id: str

    @computed_field
    @property
    def type_name(self) -> str:
        return self.type.__name__

    @property
    def type(self) -> Type[T]:
        return self.__pydantic_generic_metadata__["args"][0]

    @validate_call(validate_return=True)
    def get(self) -> Optional[T]:
        # Connect to your registry system
        registry = current_registry.get()
        if registry is None:
            return None

        # Get the registrant from the registry
        registrant = registry.get_registrant(self.id)

        # Type checking
        if registrant is None:
            return None

        if not isinstance(registrant, self.type):
            raise TypeError(
                f"Expected type {self.type_name}, got {type(registrant).__name__}"
            )
        return registrant


def _test():
    # Example usage

    class MyCustomRegistrant(Registrant):
        _registry_type: ClassVar[str] = "CustomType"
        data: List[str]

    # Create a specialized registry for your custom type
    my_registry = Registry[MyCustomRegistrant]()

    with registry_context(my_registry):
        # Create and automatically register the custom registrant
        custom_item = MyCustomRegistrant(id="custom1", data=["a", "b", "c"])

        # Retrieve it from the registry
        retrieved = my_registry.get_registrant("custom1")
        if retrieved:
            print(retrieved.data)  # Outputs: ['a', 'b', 'c']
        print("Current registry:", get_current_registry().model_dump_json(indent=4))


if __name__ == "__main__":
    _test()
