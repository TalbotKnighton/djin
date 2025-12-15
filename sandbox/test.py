import pydantic as pyd
from djin.base import immutable, mutable


class Registrant(pyd.BaseModel):
    model_config = pyd.ConfigDict(frozen=True)
    names: list[str] = pyd.Field(
        default_factory=list,
        description="A list of registrant names",
        frozen=True,
    )


class Registry(pyd.BaseModel):
    model_config = pyd.ConfigDict(frozen=True)
    elements: dict[str, int] = pyd.Field(
        default_factory=dict,
        description="A dictionary mapping strings to integers",
        frozen=True,
    )


r = Registry()
r.elements["a"] = 5  # This should raise an error since the model is immutable
print(r)
