from typing import Annotated
import pydantic as pyd

# ID = Annotated[int | str]
ID = int | str


class A(pyd.BaseModel):
    id: int | str


print(A(id=0).model_dump_json())

print(A.model_validate_json(A(id=0).model_dump_json()).model_dump_json())
