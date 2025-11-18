"""
Standardizes the naming conventions of dynamic model outputs so that 
pre-built filters and processing routines can be defined.

Example pre-built convenience methods include:

- Request object pose (positiona and rotation)
- Filtering output file data and converting to usable objects (e.g. filtering down to the orientation data for a single cobject and converting the quaternion component columns to scipy rotation object).
- Etc.
"""
from __future__ import annotations

# Standard package imports
from enum import StrEnum, auto
from typing import Union, Type

# Local package imports
from djin.type_annotations import Self

class Component(StrEnum):
    """
    Defines the various 3d and 4d components needed for vectors and quaternions.

    Attributes:
        x (str): x-component
        y (str): y-component
        z (str): z-component
        q1 (str): quaternion i-component
        q2 (str): quaternion j-component
        q3 (str): quaternion k-component
        q4 (str): quaternion scalar component
    """
    x = auto()
    y = auto()
    z = auto()
    q1 = auto()
    q2 = auto()
    q3 = auto()
    q4 = auto()

class Flag(StrEnum):
    """
    Defines flags used to encode data into the output names to be used as pandas `DataFrame` column header strings.

    These flags are designed to be compatible with the `DataFrame` regex filter method.
    The descriptions of the flags are quite generic and may be a bit esoteric below.

    Attributes:
        frame (str): Signifies a reference frame
        body (str): Signifies a massive body
        force (str): Signifies a calculated force output
        torque (str): Signifies a calculated torque output
        relative_to (str): Signifies that the quantity is calcualted relative to some other frame, body, etc.
        calcualted_in_frame (str): Signifies that the quantity is calculated in a given frame
        output_in_frame (str): Signifies that the quantity is output in a given frame
        component (str): Signifies that a particular component is being represented
        angular_momentum (str): Signifies an angular momentum output
    """
    frame = '_F'
    body = '_b'
    force = '_f'
    torque = '_t'
    relative_to = '_r2'
    calculated_in_frame = '_cif'
    output_in_frame = '_oif'
    component = '_c'
    angular_momentum = '_L'

def to_title_case(string: Union[StrEnum, Filter, str, None]) -> str:
    """
    Converts snake case or missing spaces to title case in order to compactify the name of an output

    Args:
        string (StrEnum, Filter, str, None): String to be compactified by converting to title case.
            Empty string will be returned if `string` is None.
            StrEnum.value will be used if possible.

    Returns:
        (str): A formated title case string (or `''` if string is `None`)
    """
    if string is not None:
        if isinstance(string, StrEnum):
            string = string.value
        return str(string).replace('_', ' ').title().replace(' ', '')
    else:
        return ''


class Filter:
    """
    Generates filter strings for various searches using the apropriate 
    [Flag][dynamics_engine.output_naming_conventions.Flag]
    and 
    [Component][dynamics_engine.output_naming_conventions.Component]
    enumerations along with a given name or object.
    
    """
    @property
    def _constructor(self) -> Type[Self]:
        return type(self)
    
    def __init__(self, _str: str) -> None:
        self._str = _str

    def __str__(self) -> str:
        return self._str
    
    __repr__ = __str__
    
    def __add__(self, other) -> Type[Self]:
        """
        Produces a string concatenation.
        """
        return self._constructor(self._str + str(other))
    
    @classmethod
    def component(cls, name: Union[Component, str]) -> Filter:
        """
        Returns the filter for a given component

        Args:
            name (Union[Component, str]): component name
        """
        return cls(Flag.component.value + to_title_case(name))# name.value if isinstance(name, Component) else str(name))
    
    @classmethod
    def frame(cls, name: Union[Filter, str]) -> Filter:
        """
        Returns the filter corresponding to a frame of the given name

        Args:
            name (Union[Filter, str]): name of a frame
        """
        return cls(Flag.frame.value + to_title_case(name))
    
    @classmethod
    def body(cls, name: Union[Filter, str]):
        """
        Returns the filter corresponding to a body of the given name

        Args:
            name (Union[Filter, str]): name of a body
        """
        return cls(Flag.body.value + to_title_case(name))

    @classmethod
    def force(cls, name: Union[Filter, str]):
        """
        Returns the filter corresponding to a force of the given name

        Args:
            name (Union[Filter, str]): name of a force
        """
        return cls(Flag.force.value + to_title_case(name))

    @classmethod
    def torque(cls, name: Union[Filter, str]):
        """
        Returns the filter corresponding to a torque of the given name

        Args:
            name (Union[Filter, str]): name of a torque
        """
        return cls(Flag.torque.value + to_title_case(name))
    
    @classmethod
    def angular_momentum(cls, component: Union[Component, Filter, str, None]=None):
        """
        Returns the filter corresponding to angular momentum of the given component.
        If no component is given, returned filter string matches all components.

        Args:
            component (Union[Component, Filter, str, None]): name of angular momentum component.
                If no component is given, returned filter string matches all components.
        """
        return cls(Flag.angular_momentum.value + to_title_case(component))
    
    @classmethod
    def relative_to(cls, name: Union[Filter, str]):
        """
        Returns the filter for header signifying that 
        a quantity is calculated relative to some named object.

        Args:
            name (Union[Filter, str]): name of object relative to which the desired quantity is given.
        """
        return cls(Flag.relative_to.value + to_title_case(name))
    
    @classmethod
    def calculated_in_frame(cls, name: Union[Filter, str]):
        """
        Returns the filter for header signifying that 
        a quantity is calculated in a given named [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame].

        Args:
            name (Union[Filter, str]): name of [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] in which the desired quantity is calcualted.
        """
        return cls(Flag.calculated_in_frame.value + to_title_case(name))
    
    @classmethod
    def output_in_frame(cls, name: Union[Filter, str]):
        """
        Returns the filter for header signifying that 
        a quantity is calculated in a expressed in a given named [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame].

        Args:
            name (Union[Filter, str]): name of [DynamicFrame][dynamics_engine.elements.dynamic_elements.dynamic_frame.DynamicFrame] in which the desired quantity is expressed.
        """
        return cls(Flag.output_in_frame.value + to_title_case(name))
    
if __name__ == '__main__':
    print([e.value for e in Component])