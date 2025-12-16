from __future__ import annotations

from djin import containers as co
from typing import Annotated, Literal
from pydantic import BaseModel, Field


class A(BaseModel, co.Stowable):
    type: Literal["A"] = "A"
    data: float
    b_id: co.ID


class B(BaseModel, co.Stowable):
    type: Literal["B"] = "B"
    data: float
    a_id: co.ID


CatalogueAB = Annotated[
    A | B,
    Field(discriminator="type"),
]

WarehouseAB = co.Warehouse[CatalogueAB]

with WarehouseAB(id="wh").set_context() as wh:
    b_id = "some_reserved"  # TODO: better ID reservation process
    a = A(
        data=0,
        b_id=b_id,
    ).stow()
    b = B(
        data=1,
        a_id=a.id,
    ).stow(id=b_id)

    dump1 = wh.model_dump_json(indent=4)
    reloaded = WarehouseAB.model_validate_json(dump1)
    dump2 = reloaded.model_dump_json(indent=4)

    print(dump1)
    print(dump2)
    print(f"{dump1 == dump2 = }")
