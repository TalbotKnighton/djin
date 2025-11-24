from __future__ import annotations
import pydantic as pyd

from contextlib import contextmanager
import contextvars
from typing import (
    Iterator,
    List,
    Literal,
    Type,
    Self,
    Annotated,
    ClassVar,
    TypeVar,
    Generic,
    Optional,
    cast,
    get_args,
    Any,
)

__all__ = [
    "set_context_registry",
    "get_context_registry",
]


def get_named_type_generic(self: pyd.BaseModel, name: str) -> Any:
    type_generics = next(
        (
            _
            for _ in self.__orig_bases__  # type: ignore
            if hasattr(_, "__origin__") and issubclass(_.__origin__, Generic)
        ),
        None,
    )
    if type_generics is None:
        raise TypeError("Type T must be specified for Reference")
    # Get the index of the generic type T
    i = [_.__name__ for _ in get_args(type_generics)].index(name)
    return self.__pydantic_generic_metadata__["args"][i]


class RegistrantID(pyd.BaseModel):
    model_config = pyd.ConfigDict(extra="forbid", frozen=True)

    system: Optional[str] = None
    subsystem: Optional[str] = None
    component: Optional[str] = None


class Registrant(pyd.BaseModel):
    model_config = pyd.ConfigDict(extra="allow", frozen=False)

    id: RegistrantID = pyd.Field(
        default_factory=RegistrantID,
        description="Unique identifier for the registrant",
    )

    @pyd.computed_field
    @property
    def type_name(self) -> str:
        return self.type.__name__

    @property
    def type(self) -> Type[Self]:
        return type(self)

    def register(self, registry: Registry | None = None) -> Self:
        if registry is None:
            self._register_to_context_registry()
        else:
            registry.set_registrant(self)
        return self

    def _register_to_context_registry(self) -> Self:
        context_registry = get_context_registry(t=type(self))  # type: ignore
        if context_registry is not None:
            context_registry.set_registrant(self)
        return self


T = TypeVar("T", bound=Registrant)


class Registry(Registrant, Generic[T]):
    model_config = pyd.ConfigDict(extra="forbid", frozen=False)

    registrants: dict[RegistrantID, T] = {}

    @pyd.validate_call
    def get_registrant(self, id: RegistrantID) -> T | None:
        registrant_type = get_named_type_generic(
            self,
            "T",
        )  # Ensure type T is specified
        value = self.registrants.get(id, None)
        if value is None:
            return None
        else:
            if not isinstance(value, registrant_type):
                raise TypeError(
                    f"Expected registrant of type {registrant_type.__name__}, got {type(value).__name__}"
                )
            else:
                return cast(T, value)

    # @pyd.validate_call
    def set_registrant(self, registrant: T) -> None:
        registry_type_generic = get_named_type_generic(
            self,
            "T",
        )
        if not isinstance(registrant, registry_type_generic):
            raise TypeError(
                f"Expected registrant of type {registry_type_generic.__name__}, got {type(registrant).__name__}"
            )
        if registrant.id in self.registrants:
            raise ValueError(f"Registrant with name '{registrant.id}' already exists.")
        self.registrants[registrant.id] = registrant


# 3. Now properly initialize with the correct type
# Use string literals for the type argument to avoid reference before definition

G = TypeVar("G", bound=Registry)

_context_registry = contextvars.ContextVar[Registry | None](
    "_context_registry",
    default=None,
)


@contextmanager
def set_context_registry(registry: G) -> Iterator[G]:
    """
    Context manager for setting the current registry.

    Args:
        registry: The registry to use within this context

    Yields:
        (Registry[T]): The registry that was set for the context
    """
    if not isinstance(registry, Registry):
        raise TypeError(f"Expected Registry instance, got {type(registry).__name__}")

    token = _context_registry.set(registry)
    try:
        yield registry
    finally:
        _context_registry.reset(token)


def get_context_registry(t: Type[T]) -> Registry[T] | None:
    """
    Get the current registry from the context.

    Returns:
        The current registry or None if no registry is set
    """
    if not issubclass(t, Registrant):
        raise TypeError(f"Type {t} is not a subclass of Registry")
    return _context_registry.get()


class Reference(pyd.BaseModel, Generic[T]):
    model_config = pyd.ConfigDict(
        arbitrary_types_allowed=False,
        frozen=True,
    )
    # type: Annotated[str, pyd.BeforeValidator(get_type_name)]
    id: RegistrantID

    @pyd.computed_field
    @property
    def type_name(self) -> str:
        return self.type.__name__

    @property
    def type(self) -> Type[T]:
        # return self.__pydantic_generic_metadata__["args"][0]
        return get_named_type_generic(self, "T")

    @pyd.validate_call(
        validate_return=True
    )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
    def get_optional(self, registry: Optional[Registry] = None) -> Optional[T]:
        if registry is None:
            _registry = get_context_registry(t=self.type)
            if _registry is None:
                raise ValueError(
                    "No context registry is set. Please provide a registry."
                )
        else:
            _registry = registry
        return_val = _registry.get_registrant(id=self.id)
        if not isinstance(return_val, self.type) and return_val is not None:
            raise TypeError(
                f"Expected type {self.type_name}, got {type(return_val).__name__}"
            )
        return return_val

    @pyd.validate_call(
        validate_return=True
    )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
    def get(self, registry: Optional[Registry] = None) -> T:
        return_val = self.get_optional(registry=registry)
        if return_val is None:
            raise ValueError(
                f"No instance found for id {self.id} of type {self.type_name}"
            )
        return return_val

    @pyd.model_validator(mode="before")
    @classmethod
    def remove_properties(cls, values: dict) -> dict:
        for p in cls.model_computed_fields:
            if p in values:
                del values[p]
        return values


def ref(type: Type[T], id: RegistrantID) -> Reference[T]:
    return Reference[type](id=id)


def _test():
    # Example usage

    class A(Registrant):
        _registry_type: ClassVar[Literal["A"]] = "A"
        data: List[str]
        ref: Optional[Reference[A]] = None

    class B(Registrant):
        _registry_type: ClassVar[Literal["B"]] = "B"
        data: List[str]

    # Create a specialized registry for your custom type
    my_registry = Registry[B](id=RegistrantID(component="my_registry"))

    with set_context_registry(my_registry):
        # Create and automatically register the custom registrant

        with set_context_registry(
            Registry[A](id=RegistrantID(component="my_registry2")).model_copy(deep=True)
        ):
            custom_item = A(
                id=RegistrantID(component="custom1"),
                data=["a", "b", "c"],
            ).register()
            custom_item2 = A(
                id=RegistrantID(component="custom2"),
                data=["a", "b", "c"],
                ref=ref(type=A, id=custom_item.id),
            ).register()
            cr = get_context_registry(Registry[A])
            assert cr is not None
            cr_json = cr.model_dump_json(indent=4)
            print(cr_json)
            cr_loaded: Registry[A] = Registry[A].model_validate_json(cr_json)
            assert cr_loaded.model_dump_json() == cr.model_dump_json()
            ci2_loaded = cr_loaded.get_registrant(custom_item2.id)
            assert ci2_loaded is not None
            r = ci2_loaded.ref
            assert r is not None
            s = r.get()
            print(s.data)
            print("Nice!")
        custom_item = B(
            id=RegistrantID(component="custom2"),
            data=["a", "b", "c"],
        )
        custom_item.register()  # Explicitly register to context registry
        # Retrieve it from the registry
        retrieved = my_registry.get_registrant(RegistrantID(component="custom1"))
        # if retrieved:
        #     print(retrieved.data)  # Outputs: ['a', 'b', 'c']
        print(
            "model registry:\n",
            get_context_registry(Registry[Registrant]).model_dump_json(indent=4),
        )


if __name__ == "__main__":
    _test()
