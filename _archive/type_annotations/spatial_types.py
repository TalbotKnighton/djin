"""
Defines several type variables useful for mathematical objects in 6DOF dynamics calculations.
Most of the time, these will be implemented in the code as numpy arrays,
but in general, they could be any iterable such as a tuple or list.
To avoid runtime errors, it is good practice to 
type-cast or use the `.as_array()` method (where available)
for variables type hinted with the following 
definitions to a numpy array before doing array operations.
"""
from __future__ import annotations

# Standard package imports
from typing import TypeVar, Annotated, Iterable

__all__ = ['Length3Iterable', 'Length4Iterable', 'Length6Iterable', 'Tensor3x3']

T = TypeVar(name='T')

Length3Iterable = Annotated[Iterable[T], 3]
"""
Length3Iterable indicates a 3d vector (usually a numpy array)
"""
Length4Iterable = Annotated[Iterable[T], 4]
"""
Length3Iterable indicates a quaternion usually
"""
Length6Iterable = Annotated[Iterable[T], 6]
"""
Length3Iterable indicates a combination of linear and angular quantities.  That is
a generalized load vector (forces and torques) or velocity vector (linear and angular), 
etc.
"""
Tensor3x3 = Annotated[Iterable[T], [3, 3]]
"""
A 3x3 tensor is used for the inertia tensor.  Usually this would be a numpy array, but
it could also be a set of nested lists (to be converted to numpy array for matrix multipleication).
"""
