from __future__ import annotations
import numpy as np
import pydantic as pyd

from contextlib import contextmanager
import contextvars
from typing import (
    Annotated,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Literal,
    Tuple,
    Type,
    Self,
    TypeVar,
    Generic,
    Optional,
    Union,
    cast,
    get_args,
    Any,
    overload,
)
from djin.base import immutable, mutable

__all__ = [
    # "set_context_registry",
    # "get_context_registry",
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


def get_origin(t: Any) -> Generator[Any, None, None]:
    """
    Recursively extract origin types from a type annotation.

    This function yields all origin types within a complex type annotation,
    such as those from typing module (List, Dict, Union, etc.).

    Args:
        t: A type annotation to extract origins from

    Yields:
        Origin types found within the type annotation
    """
    # Get attributes if they exist
    origin = getattr(t, "__origin__", None)
    args = getattr(t, "__args__", None)

    # Base case: if it's a simple type (no origin or args)
    if origin is None and args is None:
        yield t
        return

    # If it has an origin but no args
    if origin is not None and args is None:
        yield origin
        return

    # If it has an origin, yield it
    if origin is not None:
        # unannotated types such as Union have origins,
        # but we don't want to yield them
        pass

    # Recursively process all args
    if args is not None:
        for arg in args:
            yield from get_origin(arg)


def validate_against_named_generic(model: pyd.BaseModel, obj: Any, typevar: TypeVar):
    generic_type = get_named_type_generic(model, typevar.__name__)
    _type: tuple[Type] = tuple(get_origin(generic_type))
    # _type = _type[0] if len(_type) == 1 else _type
    try:
        if not isinstance(obj, _type):
            raise pyd.ValidationError
    except TypeError:
        breakpoint()


RT = TypeVar("RT")


# @mutable
# class Contents(pyd.BaseModel, Generic[RT]):
#     contents: Optional[RT] = None

# def push(self, obj: RT) -> Self:
#     self.space = obj
#     return self

# def pop_optional(self) -> Optional[RT]:
#     registrant_type = get_named_type_generic(self, RT.__name__)
#     obj = self.space
#     if obj is None:
#         return None
#     else:
#         if not isinstance(obj, registrant_type):
#             raise TypeError(
#                 f"Expected registrant of type {registrant_type.__name__}, got {type(value).__name__}"
#             )
#         else:
#             return cast(RT, obj)


# def pop(self) -> RT:
#     obj = self.pop_optional()
#     if obj is None:
#         raise
#     return obj
ID = str | int


@mutable
class Container(pyd.BaseModel, Generic[RT]):
    model_config = pyd.ConfigDict(extra="forbid")
    type: Literal["container"] = "container"
    id: ID = pyd.Field(
        description="Unique identifier for the container",
    )
    contents: Optional[RT] = None

    # @pyd.model_validator(mode="before")
    # @classmethod
    # def remove_properties(cls, values: dict) -> dict:
    #     for p in cls.model_computed_fields:
    #         if p in values:
    #             del values[p]
    #     return values

    # def get_contents(self):
    #     if self.contents is None:
    #         raise
    #     else:
    #         return self.contents
    # def _stow_to_context_space(self) -> Self:
    #     context_registry = get_context_registry(t=type(self))  # type: ignore
    #     if context_registry is not None:
    #         context_registry.(self)
    #     return self


def to_int(obj: str | int) -> int:
    try:
        return int(obj)
    except ValueError:
        return -1


@immutable
class Warehouse(Container, Generic[RT]):
    contents: dict[ID, Container[RT]] = pyd.Field(
        default_factory=dict[ID, Container[RT]]
    )

    def get_next_id(self) -> int:
        return int(np.max([to_int(k) for k in self.contents.keys()])) + 1

    @pyd.validate_call(validate_return=True)
    def put(
        self,
        container: Container[RT],
        override: bool = False,
    ):
        if not isinstance(container, Container):
            raise pyd.ValidationError
        if (not override) and (container.id in self.contents):
            raise ValueError(f"ID {container.id = } exists")
        validate_against_named_generic(
            model=self,
            obj=container.contents,
            typevar=RT,
        )
        self.contents[container.id] = container
        return container

    @pyd.validate_call(validate_return=True)
    def get_optional(self, id: ID) -> Optional[Container[RT]]:
        return self.contents.get(id, None)

    @pyd.validate_call(validate_return=True)
    def get(self, id: ID) -> Container[RT]:
        container = self.get_optional(id)
        if container is None:
            raise ValueError(f"Container ID {id = } not found")
        return container

    @pyd.validate_call(validate_return=True)
    def pack(
        self,
        id: Optional[ID] = None,
        contents: Optional[RT] = None,
    ):
        return self.put(
            container=Container[RT](
                id=id if id is not None else self.get_next_id(),
                contents=contents,
            )
        )

    @pyd.validate_call(validate_return=True)
    def unpack_optional(self, id: ID) -> Optional[RT]:
        return self.get(id).contents

    @pyd.validate_call(validate_return=True)
    def unpack(self, id: ID) -> RT:
        contents = self.unpack_optional(id=id)
        if contents is None:
            raise ValueError(f"You tried to unpack an empty container, {id = }")
        return contents


# class TypedID(pyd.BaseModel, Generic[RT]):
#     """"""


class _test1:
    class A(pyd.BaseModel):
        my_type: Literal["a"] = "a"

    class B(pyd.BaseModel):
        my_type: Literal["b"] = "b"
        subtype: Literal["1"] = "1"

    class C(pyd.BaseModel):
        my_type: Literal["b"] = "b"
        subtype: Literal["2"] = "2"

    Universe = Annotated[
        A
        | Annotated[
            B | C,
            pyd.Field(discriminator="subtype"),
        ],
        pyd.Field(discriminator="my_type"),
    ]

    warehouse = Warehouse[Universe](
        id="universe",
        contents={},
    )

    @classmethod
    def test(cls):
        # print(list(get_origin(Universe)))
        # print(get_origin(A))
        print(cls.warehouse)
        cls.warehouse.put(Container(id="hi", contents=cls.A()))
        cls.warehouse.pack(id="hi2", contents=cls.A())
        cls.warehouse.pack(contents=cls.A())
        cls.warehouse.pack(contents=cls.B())
        print(cls.warehouse.get(id="hi"))
        print(cls.warehouse.unpack(id="hi").model_dump_json(indent=4))
        print(cls.warehouse)
        print("\n\n")
        wh = Warehouse[cls.Universe].model_validate_json(
            cls.warehouse.model_dump_json()
        )

        print()
        print(
            Warehouse[cls.Universe]
            .model_validate_json(cls.warehouse.model_dump_json())
            .model_dump_json(indent=4)
        )


if __name__ == "__main__":
    _test1.test()


@immutable
class Ref(pyd.BaseModel, Generic[RT]):
    type_discriminator: Literal["reference"] = "reference"
    id: str

    @property
    def type(self) -> Type[RT]:
        # return self.__pydantic_generic_metadata__["args"][0]
        return get_named_type_generic(self, RT.__name__)

    @pyd.validate_call(
        validate_return=True
    )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
    def get_optional(
        self,
        warehouse: Warehouse,
    ) -> Optional[Container[RT]]:
        return_val = warehouse.get_optional(id=self.id)
        # TODO clean this up.  What am I checking?  Container type or container contents?
        if return_val is not None and return_val.contents is not None:
            validate_against_named_generic(
                model=self,
                obj=return_val.contents,
                typevar=RT,
            )
        return return_val

    @pyd.validate_call(
        validate_return=True
    )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
    def get(
        self,
        warehouse: Warehouse,
    ) -> Container[RT]:
        return_val = self.get_optional(warehouse=warehouse)
        if return_val is None:
            raise ValueError(f"No Container found for id {self.id}")
        return return_val

    @pyd.validate_call(
        validate_return=True
    )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
    def unpack_optional(
        self,
        warehouse: Warehouse,
    ) -> Optional[RT]:
        return_val = warehouse.unpack_optional(id=self.id)
        if return_val is not None:
            validate_against_named_generic(
                model=self,
                obj=return_val,
                typevar=RT,
            )
        return return_val

    @pyd.validate_call(
        validate_return=True
    )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
    def unpack(
        self,
        warehouse: Warehouse,
    ) -> RT:
        return_val = self.unpack_optional(warehouse=warehouse)
        if return_val is None:
            raise ValueError(f"No instance found for id {self.id}")
        return return_val


def ref(type: Type[RT], id: str) -> Ref[RT]:
    return Ref[type](id=id)


class _test2:
    class A(pyd.BaseModel):
        mytype: Literal["a"] = "a"
        ref: Ref[_test2.B]

    class B(pyd.BaseModel):
        mytype: Literal["b"] = "b"
        ref: Ref[_test2.A]

    Universe = Annotated[
        A | B,
        pyd.Field(discriminator="mytype"),
    ]

    UW = Warehouse[Universe]

    @classmethod
    def test(cls):
        cls.UW.model_rebuild()
        A = cls.A
        B = cls.B
        uw = cls.UW(id="universal_warehouse")
        uw.pack(id="a", contents=A(ref=ref(type=B, id="b")))
        uw.pack(id="b", contents=B(ref=ref(type=A, id="a")))
        print(uw.model_dump_json(indent=4))


if __name__ == "__main__":
    _test2.test()


# T = TypeVar("T", bound=Registrant)


# def get_discriminator_value(v: Any) -> str:
#     if isinstance(v, dict):
#         return str(v.get("type_discriminator"))
#     return str(getattr(v, "type_discriminator", None))


# @immutable
# class Space(Container, Generic[RT]):
#     model_config = pyd.ConfigDict(extra="forbid")

#     containers: dict[str, Container[RT]] = pyd.Field(
#         default_factory=dict,
#         description="Dictionary of registrants by their unique identifier",
#     )

#     @pyd.validate_call
#     def get_container(self, id: str) -> RT | None:
#         # registrant_type = get_named_type_generic(
#         #     self,
#         #     RT.__name__,
#         # )  # Ensure type T is specified
#         # value = self.registrants.get(id, None)
#         # if value is None:
#         #     return None
#         # else:
#         #     if not isinstance(value, registrant_type):
#         #         raise TypeError(
#         #             f"Expected registrant of type {registrant_type.__name__}, got {type(value).__name__}"
#         #         )
#         #     else:
#         #         return cast(RT, value)
#         c = self.containers.get(id, None)
#         if c
#         return

#     # @pyd.validate_call
#     def stowe_container(self, registrant: T) -> None:
#         registry_type_generic = get_named_type_generic(
#             self,
#             "T",
#         )
#         if not isinstance(registrant, registry_type_generic):
#             raise TypeError(
#                 f"Expected registrant of type {registry_type_generic.__name__}, got {type(registrant).__name__}"
#             )
#         if registrant.id in self.index:
#             raise ValueError(f"Registrant with name '{registrant.id}' already exists.")
#         self.index[registrant.id] = registrant


# 3. Now properly initialize with the correct type
# Use string literals for the type argument to avoid reference before definition

# G = TypeVar("G", bound=Space)

# _context_registry = contextvars.ContextVar[Space | None](
#     "_context_registry",
#     default=None,
# )


# @contextmanager
# def set_context_registry(registry: G) -> Iterator[G]:
#     """
#     Context manager for setting the current registry.

#     Args:
#         registry: The registry to use within this context

#     Yields:
#         (Registry[T]): The registry that was set for the context
#     """
#     if not isinstance(registry, Space):
#         raise TypeError(f"Expected Registry instance, got {type(registry).__name__}")

#     token = _context_registry.set(registry)
#     try:
#         yield registry
#     finally:
#         _context_registry.reset(token)


# def get_context_registry(t: Type[T]) -> Space[T] | None:
#     """
#     Get the current registry from the context.

#     Returns:
#         The current registry or None if no registry is set
#     """
#     if not issubclass(t, Container):
#         raise TypeError(f"Type {t} is not a subclass of Registry")
#     return _context_registry.get()


# class Reference(pyd.BaseModel, Generic[T]):
#     model_config = pyd.ConfigDict(
#         arbitrary_types_allowed=False,
#         frozen=True,
#     )
#     # type: Annotated[str, pyd.BeforeValidator(get_type_name)]
#     id: str

#     @pyd.computed_field
#     @property
#     def type_name(self) -> str:
#         return self.type.__name__

#     @property
#     def type(self) -> Type[T]:
#         # return self.__pydantic_generic_metadata__["args"][0]
#         return get_named_type_generic(self, "T")

#     @pyd.validate_call(
#         validate_return=True
#     )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
#     def get_optional(self, registry: Optional[Space] = None) -> Optional[T]:
#         if registry is None:
#             _registry = get_context_registry(t=self.type)
#             if _registry is None:
#                 raise ValueError(
#                     "No context registry is set. Please provide a registry."
#                 )
#         else:
#             _registry = registry
#         return_val = _registry.get_container(id=self.id)
#         if not isinstance(return_val, self.type) and return_val is not None:
#             raise TypeError(
#                 f"Expected type {self.type_name}, got {type(return_val).__name__}"
#             )
#         return return_val

#     @pyd.validate_call(
#         validate_return=True
#     )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
#     def get(self, registry: Optional[Space] = None) -> T:
#         return_val = self.get_optional(registry=registry)
#         if return_val is None:
#             raise ValueError(
#                 f"No instance found for id {self.id} of type {self.type_name}"
#             )
#         return return_val

#     @pyd.model_validator(mode="before")
#     @classmethod
#     def remove_properties(cls, values: dict) -> dict:
#         for p in cls.model_computed_fields:
#             if p in values:
#                 del values[p]
#         return values


# def ref(type: Type[T], id: str) -> Reference[T]:
#     return Reference[type](id=id)


# def _test():
#     # Example usage

#     class A(Container):
#         type_discriminator: Literal["A"]
#         data: List[str]
#         ref: Optional[Reference[A]] = None

#     class B(Container):
#         data: List[str]

#     # Create a specialized registry for your custom type
#     my_registry = Space[B](id="my_registry")

#     with set_context_registry(my_registry):
#         # Create and automatically register the custom registrant

#         with set_context_registry(Space[A](id="my_registry2").model_copy(deep=True)):
#             custom_item = A(
#                 id="custom1",
#                 data=["a", "b", "c"],
#             ).put_to()
#             custom_item2 = A(
#                 id="custom2",
#                 data=["a", "b", "c"],
#                 ref=ref(type=A, id=custom_item.id),
#             ).put_to()
#             cr = get_context_registry(Space[A])
#             assert cr is not None
#             cr_json = cr.model_dump_json(indent=4)
#             print(cr_json)
#             cr_loaded: Space[A] = Space[A].model_validate_json(cr_json)
#             assert cr_loaded.model_dump_json() == cr.model_dump_json()
#             ci2_loaded = cr_loaded.get_container(custom_item2.id)
#             assert ci2_loaded is not None
#             r = ci2_loaded.ref
#             assert r is not None
#             s = r.get()
#             print(s.data)
#             print("Nice!")
#         custom_item = B(
#             id="custom2",
#             data=["a", "b", "c"],
#         )
#         custom_item.put_to()  # Explicitly register to context registry
#         # Retrieve it from the registry
#         retrieved = my_registry.get_container("custom1")
#         if retrieved:
#             print(retrieved.data)  # Outputs: ['a', 'b', 'c']
#         active_registry = get_context_registry(Space[Container])
#         assert active_registry is not None
#         print(
#             "model registry:\n",
#             active_registry.model_dump_json(indent=4),
#         )


# if __name__ == "__main__":
#     _test()
