import contextvars
from typing import Optional, Generic, Type, TypeVar, Union
import typing

import pydantic as pyd
from djin.registry.core import Registry, Registrant

T = TypeVar("T", bound=Registrant)


current_registry = contextvars.ContextVar[Optional[Registry]](
    "current_registry",
    default=None,
)


class MyClass(Registrant):
    pass


x = Reference[MyClass](id="123")
print(x.get())
# print(x.model_dump_json())
# y = Reference[MyClass].model_validate_json(x.model_dump_json())
# print(y.get())
