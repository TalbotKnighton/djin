from __future__ import annotations
import pydantic as pyd
from typing import Annotated, Literal

from djin.containers.core import Ref, Warehouse, ref


class A(pyd.BaseModel):
    mytype: Literal["a"] = "a"
    ref: Ref[B]


class B(pyd.BaseModel):
    mytype: Literal["b"] = "b"
    ref: Ref[A]


Universe = Annotated[
    A | B,
    pyd.Field(discriminator="mytype"),
]

UW = Warehouse[Universe]
UW.model_rebuild()
uw = UW(id="universal_warehouse")
a = A(ref=ref(type=B, id="b"))
uw.pack(id="a", contents=a)
uw.pack(id="b", contents=B(ref=ref(type=A, id="a")))
b = a.ref.unpack(warehouse=uw)
print(uw.model_dump_json(indent=4))
print(type(b), b.model_dump_json(indent=4))
