"""
Defines commonly used type annotations

Attributes:
    Array1D (TypeVar): 1-dimensional array of any length
    Array2D (TypeVar): 2-dimensional array of any length
"""
from typing import TypeVar, Annotated, Iterable

__all__ = ['Array1D', 'Array2D']

T = TypeVar(name='T')

Array1D = Annotated[Iterable[T], any]
Array2D = Annotated[Iterable[Iterable[T]], any]
