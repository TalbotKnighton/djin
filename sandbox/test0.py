from typing import Optional, Generic, Type, TypeVar, Union
import pydantic as pyd

T = TypeVar("T")


# def get_type_name(value: str | Type) -> str:
#     if isinstance(value, str):
#         return value
#     else:
#         return value.__name__


class Reference(pyd.BaseModel, Generic[T]):
    model_config = pyd.ConfigDict(
        arbitrary_types_allowed=False,
        frozen=True,
    )
    # type: Annotated[str, pyd.BeforeValidator(get_type_name)]
    id: str

    @pyd.computed_field
    @property
    def type_name(self) -> str:
        return self.type.__name__

    @property
    def type(self) -> Type[T]:
        return self.__pydantic_generic_metadata__["args"][0]

    @pyd.validate_call(
        validate_return=True
    )  # does not work yet https://github.com/pydantic/pydantic/issues/7796
    def get(self) -> Optional[T]:
        return_val = None  # TODO Replace with actual retrieval logic
        if return_val is None:
            return None
        if not isinstance(return_val, self.type):
            raise TypeError(
                f"Expected type {self.type_name}, got {type(return_val).__name__}"
            )
        return return_val

    @pyd.model_validator(mode="before")
    @classmethod
    def remove_properties(cls, values: dict) -> dict:
        for p in cls.model_computed_fields:
            if p in values:
                del values[p]
        return values


def ref(type: Type[T], id: str) -> Reference[T]:
    return Reference[type](id=id)


class MyClass(pyd.BaseModel):
    pass


x = ref(type=int, id="123")
Reference[int](id="123")
print(x)
print(x.model_dump_json())
y = Reference[MyClass].model_validate_json(x.model_dump_json())
print(y.get())
