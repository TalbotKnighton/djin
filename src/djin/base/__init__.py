import pydantic
from typing import Type, TypeVar


class ImmutableBaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)


class MutableBaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=False)


_T = TypeVar("_T", bound=pydantic.BaseModel)


def _update_config(cls: Type[_T], frozen_value: bool) -> Type[_T]:
    """
    Helper function to update the model_config with a frozen value.

    Args:
        cls: A Pydantic BaseModel class
        frozen_value: The value to set for the frozen flag

    Returns:
        The same class with updated model_config
    """
    # Get existing config or create a new one
    existing_config = getattr(cls, "model_config", pydantic.ConfigDict())
    existing_config.update(frozen=frozen_value)

    return cls


def mutable(cls: Type[_T]) -> Type[_T]:
    """
    Decorator to make a Pydantic model mutable.

    This decorator sets the frozen flag to False in the model_config,
    taking precedence over any existing configuration.

    Args:
        cls: A Pydantic BaseModel class

    Returns:
        The same class with updated model_config
    """
    return _update_config(cls, frozen_value=False)


def immutable(cls: Type[_T]) -> Type[_T]:
    """
    Decorator to make a Pydantic model immutable.

    This decorator sets the frozen flag to True in the model_config,
    taking precedence over any existing configuration.

    Args:
        cls: A Pydantic BaseModel class

    Returns:
        The same class with updated model_config
    """
    return _update_config(cls, frozen_value=True)
