"""
Various mathematical objects needed for dynamics calculations are defined here
"""

from __future__ import annotations

# Standard package imports
Number = float | int
import numpy as np
from scipy.spatial.transform import Rotation as ScipyRotation
from typing import (
    Type,
    Union,
    TYPE_CHECKING,
    Iterator,
    ClassVar,
    Annotated,
    Any,
    Iterable,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

# Local package imports
from djin.type_annotations import Length3Iterable, Length4Iterable, Array1D

if TYPE_CHECKING:
    from djin.frames import Frame

__all__ = ["EuclideanVector", "Quaternion", "Rotation", "Pose"]


class EuclideanVector(BaseModel):
    """
    Vector3D contains the rectilinear components of a 3D vector.
    It can be treated as an iterable or as a model.

    Args:
        x (Number): x component
        y (Number): y component
        z (Number): z component

    Allowed math operations:

        - Negation

    """

    x: Number
    y: Number
    z: Number

    model_config = ConfigDict(frozen=True)

    def __len__(self) -> int:
        return 3

    def __iter__(self) -> Iterator[Number]:
        return iter((self.x, self.y, self.z))

    def __neg__(self) -> EuclideanVector:
        return type(self).from_array(-self.as_array())

    @classmethod
    def from_array(cls, array: Length3Iterable[Number]) -> EuclideanVector:
        """
        Returns a new `Vector3D` instance from a length 3 iterable (such as a number array or list).

        Returns:
            (Vector3D): new `Vector3D` instance
        """
        return cls(x=array[0], y=array[1], z=array[2])

    def as_array(self) -> Array1D:
        """
        Returns:
            (Array1D):  Length 3 numpy array of `x, y, z` coordinates
        """
        return np.array([self.x, self.y, self.z])

    def as_pure_quat(self) -> "Quaternion":
        """
        Returns a `Quaternion` instance with scalar component 0 (pure quaternion).

        Returns:
            (Quaternion): new pure quaternion (zero scalar component)
        """
        return Quaternion.from_components(vector=self, scalar=0)

    @classmethod
    def null(cls) -> EuclideanVector:
        """
        Returns a new Vector3D instance with components set to zero

        Returns:
            (Vector3D): new Vector3D instance with components set to zero
        """
        return cls(x=0, y=0, z=0)

    @property
    def _constructor(self) -> Type[EuclideanVector]:
        """
        Returns the constructor for the class. This is used to create new instances of the class.
        """
        return type(self)

    def __add__(self, other: EuclideanVector) -> EuclideanVector:
        """
        Defines the addition operation against another `Vector3D` instance.
        """
        if isinstance(other, EuclideanVector):
            return self._constructor.from_array(self.as_array() + other.as_array())
        if isinstance(other, (float, int)):
            return self._constructor.from_array(self.as_array() + other)
        if isinstance(other, Iterable) and len(other) == 3:
            return self._constructor.from_array(self.as_array() + np.array(other))
        raise TypeError(
            f"Unsupported type for addition: {type(other)}. Expected Vector3D, float, int, or iterable of length 3."
        )

    def __sub__(self, other: EuclideanVector) -> EuclideanVector:
        """
        Defines the subtraction operation against another `Vector3D` instance.
        """
        if isinstance(other, EuclideanVector):
            return self._constructor.from_array(self.as_array() - other.as_array())
        if isinstance(other, (float, int)):
            return self._constructor.from_array(self.as_array() - other)
        if isinstance(other, Iterable) and len(other) == 3:
            return self._constructor.from_array(self.as_array() - np.array(other))
        raise TypeError(
            f"Unsupported type for subtraction: {type(other)}. Expected Vector3D, float, int, or iterable of length 3."
        )

    def __mul__(self, other: Union[float, int]) -> EuclideanVector:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return self._constructor.from_array(self.as_array() * other)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __rmul__(self, other: Union[float, int]) -> EuclideanVector:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return self._constructor.from_array(self.as_array() * other)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __truediv__(self, other: Union[float, int]) -> EuclideanVector:
        """
        Defines the division operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return self._constructor.from_array(self.as_array() / other)
        raise TypeError(
            f"Unsupported type for division: {type(other)}. Expected float or int."
        )


class Quaternion(BaseModel):
    """
    Defines a quaternion that can be used in math operations.

    Args:
        i (Number): i component of vector portion
        j (Number): j component of vector portion
        k (Number): k component of vector portion
        s (Number): s component
    """

    i: Number
    j: Number
    k: Number
    s: Number

    model_config = ConfigDict(frozen=True)

    def __len__(self) -> int:
        return 4

    def __iter__(self) -> Iterator[Number]:
        return iter((self.i, self.j, self.k, self.s))

    @property
    def vector(self) -> EuclideanVector:
        """
        Returns the vector portion of the quaternion.

        Returns:
            (Vector3D): Vector portion of quaternion
        """
        return EuclideanVector(x=self.i, y=self.j, z=self.k)

    @property
    def scalar(self) -> Number:
        """
        Returns the scalar portion of the quaternion

        Returns:
            (Number): Scalar portion of quaternion
        """
        return self.s

    @classmethod
    def from_array(cls, array: Length4Iterable[Number]) -> Quaternion:
        """
        Creates a new quaternion object from the given array.
        The scalar component assumed to be last.

        Returns:
            (Quaternion): new quaternion from array (scalar component last)
        """
        assert len(array) == 4
        return cls(i=array[0], j=array[1], k=array[2], s=array[3])

    def as_array(self) -> Array1D:
        """
        Returns the quaternion components as a numpy array.

        Returns:
            (Length4Iterable): Length 4 numpy array of i, j, k and scalar components in that order.
        """
        return np.array(tuple(self))

    @classmethod
    def from_components(cls, vector: EuclideanVector, scalar: Number) -> Quaternion:
        """
        Creates a new `Quaternion` instance from a vector and scalar.
        Asserts vector is length 3

        Returns:
            (Quaternion): New quaternion object.
        """
        assert len(vector) == 3
        return cls(i=vector.x, j=vector.y, k=vector.z, s=scalar)

    def __mul__(self, q: Union[Quaternion, Number]) -> Quaternion:
        """
        Defines the multiplication operation against another `Quaternion` instance or
        against a scalar.
        """
        if isinstance(q, Quaternion):
            s1 = self.s
            x1 = self.i
            y1 = self.j
            z1 = self.k
            s2 = q.s
            x2 = q.i
            y2 = q.j
            z2 = q.k

            s = s1 * s2 - x1 * x2 - y1 * y2 - z1 * z2
            x = s1 * x2 + x1 * s2 + y1 * z2 - z1 * y2
            y = s1 * y2 - x1 * z2 + y1 * s2 + z1 * x2
            z = s1 * z2 + x1 * y2 - y1 * x2 + z1 * s2

            return Quaternion(i=x, j=y, k=z, s=s)
        elif isinstance(q, Number):
            arr = self.as_array() * q
            return Quaternion(i=arr[0], j=arr[1], k=arr[2], s=arr[3])

    def __rmul__(self, q: Union[Quaternion, Number]) -> Quaternion:
        """
        Defines the multiplication operation against another `Quaternion` instance or
        against a scalar.
        """
        if isinstance(q, Quaternion):
            s1 = q.s
            x1 = q.i
            y1 = q.j
            z1 = q.k
            s2 = self.s
            x2 = self.i
            y2 = self.j
            z2 = self.k

            s = s1 * s2 - x1 * x2 - y1 * y2 - z1 * z2
            x = s1 * x2 + x1 * s2 + y1 * z2 - z1 * y2
            y = s1 * y2 - x1 * z2 + y1 * s2 + z1 * x2
            z = s1 * z2 + x1 * y2 - y1 * x2 + z1 * s2

            return Quaternion(i=x, j=y, k=z, s=s)
        elif isinstance(q, Number):
            arr = self.as_array() * q
            return Quaternion(i=arr[0], j=arr[1], k=arr[2], s=arr[3])

    def as_rotation(self) -> Rotation:
        """
        Converts the quaternion to a scipy rotation object.

        Returns:
            (Rotation): Rotation object generated from quaterion.
        """
        return Rotation.from_quat(tuple(self))

    @classmethod
    def from_rotation(cls, r: Rotation) -> Quaternion:
        """
        Creates a `Quaternion` instance from a `Rotation` object.

        Returns:
            (Quaternion): New quaternion instance from `Rotation` object.
        """
        return cls.from_array(r.as_quat())


class Rotation(BaseModel):
    """
    Pydantic-compatible wrapper around scipy.spatial.transform.Rotation
    """

    # Store the quaternion values directly
    quat: tuple[float, float, float, float] = Field(default=(0.0, 0.0, 0.0, 1.0))

    model_config = ConfigDict(
        frozen=True,
    )

    # Use properties to provide access to the ScipyRotation object
    @property
    def _rotation(self) -> ScipyRotation:
        """Get the underlying ScipyRotation object"""
        return ScipyRotation.from_quat(self.quat)

    # Factory methods
    @classmethod
    def from_quat(cls, quat):
        """Create rotation from quaternion [x, y, z, w]"""
        return cls(quat=tuple(quat))

    @classmethod
    def from_rotation(cls, rotation: ScipyRotation):
        """Create from ScipyRotation object"""
        return cls.from_quat(rotation.as_quat())

    @classmethod
    def from_euler(
        cls,
        seq: str,
        angles: tuple[float, float, float],
        degrees=False,
    ):
        """Create rotation from Euler angles"""
        return cls.from_rotation(ScipyRotation.from_euler(seq, angles, degrees))

    @classmethod
    def from_rotvec(cls, rotvec):
        """Create rotation from rotation vector"""
        return cls.from_rotation(ScipyRotation.from_rotvec(rotvec))

    @classmethod
    def from_matrix(cls, matrix):
        """Create rotation from rotation matrix"""
        return cls.from_rotation(ScipyRotation.from_matrix(matrix))

    @classmethod
    def identity(cls):
        """Create identity rotation"""
        return cls()  # Default constructor creates identity rotation

    @classmethod
    def null(cls):
        """Creates a null rotation object (same as identity)"""
        return cls.identity()

    # Access methods
    def as_quat(self):
        """Return rotation as quaternion [x, y, z, w]"""
        return np.array(self.quat)

    def as_euler(self, seq, degrees=False):
        """Return rotation as Euler angles"""
        return self._rotation.as_euler(seq, degrees)

    def as_rotvec(self):
        """Return rotation as rotation vector"""
        return self._rotation.as_rotvec()

    def as_matrix(self):
        """Return rotation as 3x3 matrix"""
        return self._rotation.as_matrix()

    # Operations
    def __mul__(self, other):
        """Compose rotations (right multiplication)"""
        if isinstance(other, Rotation):
            return Rotation.from_rotation(self._rotation * other._rotation)
        if isinstance(other, ScipyRotation):
            return Rotation.from_rotation(self._rotation * other)
        if isinstance(other, EuclideanVector):
            # Rotate vector
            rotated = self._rotation.apply(other.as_array())
            return EuclideanVector.from_array(rotated)
        if isinstance(other, (list, tuple, np.ndarray)) and len(other) == 3:
            # Rotate vector array
            return self._rotation.apply(other)
        return NotImplemented

    def inv(self):
        """Return inverse rotation"""
        return Rotation.from_rotation(self._rotation.inv())

    def magnitude(self):
        """Return the magnitude of the rotation in radians"""
        return self._rotation.magnitude()

    def mean(self, weights=None):
        """Compute the weighted mean of rotations"""
        return Rotation.from_rotation(self._rotation.mean(weights))

    def reduce(self, left=None, right=None):
        """Reduce this rotation with pre/post rotations"""
        return Rotation.from_rotation(
            self._rotation.reduce(
                left._rotation if left is not None else None,
                right._rotation if right is not None else None,
            )
        )

    def apply(self, vectors, inverse=False):
        """Apply rotation to vectors"""
        return self._rotation.apply(vectors, inverse)

    # For compatibility
    def as_scipy_rotation(self):
        """Return the underlying ScipyRotation object"""
        return self._rotation


class Pose(BaseModel):
    """
    Stores position and rotation (no frame specified)

    Attributes:
        postion (Vector3D): Position information as a `Vector3D` (no frame specified)
        rotation (Rotation): Rotation information as a `Rotation` object (no frame specified)
    """

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Attributes
    position: EuclideanVector
    rotation: Rotation

    @classmethod
    def null(cls) -> Pose:
        """
        Returns a null pose (position 0, 0, 0, and null rotation)

        Returns:
            (Pose): null pose (position and rotation of zero)
        """
        return cls(
            position=EuclideanVector.null(),
            rotation=Rotation.null(),
        )

    def as_array(self) -> Array1D:
        """
        Concatenates the position and rotation array representations together into a length 7 array.

        Returns:
            (Array1D): Numpy array of length 7 containing components x, y, z, i, j, k, s from the
                position and rotation quaternion.
        """
        return np.concatenate([self.position.as_array(), self.rotation.as_quat()])

    def change_to_frame(
        self,
        to_frame: "Frame",
        from_frame: "Frame",
    ) -> Pose:
        """
        Performs a frame transformation on the pose.

        Args:
            to_frame (Frame): Desired frame in which we want to express the Pose
            from_frame (Frame): frame in which the Pose is already expressed.

        Returns:
            (Pose): Frame-transformed pose expressed in the `to_frame`
        """
        from frames import Frame

        return (
            Frame(parent=from_frame, pose=self)
            .change_parent_frame(new_frame=to_frame)
            .pose
        )


if __name__ == "__main__":
    print(EuclideanVector.from_array([1, 2, 3]))
    print(EuclideanVector(x=1, y=2, z=3).as_pure_quat())
    print(Quaternion.from_array([1, 2, 3, 1]).as_array())
    q1 = Quaternion(i=1, j=1, k=1, s=1)
    q2 = Quaternion(i=2, j=2, k=2, s=2)
    print((q1 * q2).vector)
