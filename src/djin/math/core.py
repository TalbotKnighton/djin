from __future__ import annotations
from typing import Iterable, Self, Type
from numpydantic import NDArray, Shape
from pydantic import BaseModel, ConfigDict, Field
import numpy as np
from scipy.spatial.transform import Rotation as ScipyRotation


class VectorR3(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # Define a 1D array of length 3 with float64 dtype
    array: NDArray[Shape["3"], np.float64] = (0.0, 0.0, 0.0)

    # The Shape class already handles validation, so an additional validator is optional
    @property
    def x(self):
        return self.array[0]

    @property
    def y(self):
        return self.array[1]

    @property
    def z(self):
        return self.array[2]

    @property
    def m(self):
        return np.linalg.norm(self.array)

    def __len__(self) -> int:
        return len(self.array)

    def __iter__(self) -> Iterable[float]:
        return iter(self.array)

    def __neg__(self) -> VectorR3:
        return self._constructor(-self.array)

    @classmethod
    def from_components(
        cls,
        x: float,
        y: float,
        z: float,
    ) -> VectorR3:
        """
        Returns a new `VectorR3` instance from a length 3 iterable (such as a number array or list).

        Returns:
            (VectorR3): new `VectorR3` instance
        """
        return cls(
            [
                x,
                y,
                z,
            ]
        )

    def as_pure_quat(self) -> Quaternion:
        """
        Returns a `Quaternion` instance with scalar component 0 (pure quaternion).

        Returns:
            (Quaternion): new pure quaternion (zero scalar component)
        """
        return Quaternion.from_components(vector=self, scalar=0)

    @classmethod
    def null(cls) -> VectorR3:
        """
        Returns a new VectorR3 instance with components set to zero

        Returns:
            (VectorR3): new VectorR3 instance with components set to zero
        """
        return cls(
            vector=np.zeros(
                3,
                dtype=np.float64,
            ),
        )

    @property
    def _constructor(self) -> Type[VectorR3]:
        """
        Returns the constructor for the class. This is used to create new instances of the class.
        """
        return type(self)

    def __add__(
        self,
        other: VectorR3,
    ) -> VectorR3:
        """
        Defines the addition operation against another `VectorR3` instance.
        """
        if isinstance(other, VectorR3):
            return self._constructor(self.array + other.array)
        if isinstance(other, (float, int)):
            return self._constructor(self.array + other)
        if isinstance(other, Iterable):
            return self.__add__(self._constructor(other))
        raise TypeError(
            f"Unsupported type for addition: {type(other)}. Expected VectorR3, float, int, or iterable of length 3."
        )

    def __sub__(self, other: VectorR3) -> VectorR3:
        """
        Defines the subtraction operation against another `VectorR3` instance.
        """
        if isinstance(other, (VectorR3, float, int)):
            return self.__add__(-other)
        if isinstance(other, Iterable):
            return self.__add__(-self._constructor(other))
        raise TypeError(
            f"Unsupported type for subtraction: {type(other)}. Expected VectorR3, float, int, or iterable of length 3."
        )

    def __mul__(self, other: float | int) -> VectorR3:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return self._constructor(self.array * other)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __rmul__(self, other: float | int) -> VectorR3:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return self._constructor(other * self.array)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __truediv__(self, other: float | int) -> VectorR3:
        """
        Defines the division operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return self._constructor(self.array / other)
        raise TypeError(
            f"Unsupported type for division: {type(other)}. Expected float or int."
        )

    # def __matmul__(self, other: VectorR3 | Tensor3x3) -> float:
    #     """
    #     Defines the dot product operation against another `VectorR3` instance.
    #     """
    #     if isinstance(other, VectorR3):
    #         return self.vector @ other.vector
    #     if isinstance(other, Tensor3x3):
    #         return other._constructor(self.vector @ other.matrix)
    #     if isinstance(other, Iterable):
    #         other_array = np.array(other)
    #         if other_array.shape == (3,):
    #             return self._constructor(self.vector @ other_array)
    #         if other_array.shape == (3, 3):
    #             return Tensor3x3(self.vector @ other_array)
    #     raise TypeError(
    #         f"Unsupported type for dot product: {type(other)}. Expected VectorR3."
    #     )

    # def __rmatmul__(self, other: VectorR3 | Tensor3x3) -> float:
    #     """
    #     Defines the dot product operation against another `VectorR3` instance.
    #     """
    #     if isinstance(other, VectorR3):
    #         return self._constructor(other.vector @ self.vector)
    #     if isinstance(other, Tensor3x3):
    #         return other._constructor(other.matrix @ self.vector)
    #     raise TypeError(
    #         f"Unsupported type for dot product: {type(other)}. Expected VectorR3."
    #     )


class Tensor3x3(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # Define a 2D array of shape (3, 3) with float64 dtype
    array: NDArray[Shape["3, 3"], np.float64] = (
        (1, 0.0, 0.0),
        (0.0, 1, 0.0),
        (0.0, 0.0, 1),
    )

    def __add__(self, other: float | int | Tensor3x3) -> Tensor3x3:
        """
        Defines the addition operation against another `Tensor3x3` instance.
        """
        if isinstance(other, Tensor3x3):
            return self._constructor(self.array + other.array)
        if isinstance(other, (float, int)):
            return self._constructor(self.array + other)
        raise TypeError(
            f"Unsupported type for addition: {type(other)}. Expected Tensor3x3."
        )

    def __radd__(self, other: float | int | Tensor3x3) -> Tensor3x3:
        """
        Defines the addition operation against another `Tensor3x3` instance.
        """
        if isinstance(other, Tensor3x3):
            return Tensor3x3(other.array + self.array)
        if isinstance(other, (float, int)):
            return Tensor3x3(other + self.array)
        raise TypeError(
            f"Unsupported type for addition: {type(other)}. Expected Tensor3x3."
        )

    def __mul__(self, other: float | int) -> Tensor3x3:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return Tensor3x3(self.array * other)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __rmul__(self, other: float | int) -> Tensor3x3:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return Tensor3x3(other * self.array)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    @property
    def _constructor(self) -> Type[Tensor3x3]:
        """
        Returns the constructor for the class. This is used to create new instances of the class.
        """
        return type(self)

    # def __matmul__(self, other: VectorR3 | Tensor3x3) -> VectorR3:
    #     """
    #     Defines the matrix-vector multiplication operation against a `VectorR3` instance.
    #     """
    #     if isinstance(other, VectorR3):
    #         return other._constructor(self.matrix @ other.vector)
    #     if isinstance(other, Tensor3x3):
    #         return self._constructor(self.matrix @ other.matrix)
    #     if isinstance(other, Iterable):
    #         other_array = np.array(other)
    #         if other_array.shape == (3,):
    #             return VectorR3(self.matrix @ other_array)
    #         elif other_array.shape == (3, 3):
    #             return self._constructor(self.matrix @ other_array)
    #     raise TypeError(
    #         f"Unsupported type for matrix-vector multiplication: {type(other)}. Expected VectorR3."
    #     )

    # def __rmatmul__(self, other: VectorR3 | Tensor3x3) -> VectorR3:
    #     """
    #     Defines the matrix-vector multiplication operation against a `VectorR3` instance.
    #     """
    #     if isinstance(other, VectorR3):
    #         return other._constructor(other.vector @ self.matrix)
    #     if isinstance(other, Tensor3x3):
    #         return self._constructor(other.matrix @ other.matrix)
    #     if isinstance(other, Iterable):
    #         other_array = np.array(other)
    #         if other_array.shape == (3,):
    #             return VectorR3(other_array @ self.matrix)
    #         elif other_array.shape == (3, 3):
    #             return self._constructor(other_array @ self.matrix)
    #     raise TypeError(
    #         f"Unsupported type for matrix-vector multiplication: {type(other)}. Expected VectorR3."
    #     )


class Quaternion(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    # Define a 1D array of length 4 with float64 dtype
    array: NDArray[Shape["4"], np.float64] = (0.0, 0.0, 0.0, 1.0)

    @property
    def i(self):
        return self.array[0]

    @property
    def j(self):
        return self.array[1]

    @property
    def k(self):
        return self.array[2]

    @property
    def s(self):
        return self.array[3]

    @property
    def vector(self):
        return VectorR3(self.array[:3])

    @property
    def scalar(self):
        return self.array[3]

    @classmethod
    def from_components(cls, vector: VectorR3, scalar: float | int) -> Quaternion:
        """
        Creates a new `Quaternion` instance from a vector and scalar.
        Asserts vector is length 3

        Returns:
            (Quaternion): New quaternion object.
        """
        return cls(list(vector) + [scalar])

    def __mul__(self, other: Quaternion | Iterable | float | int) -> Quaternion:
        """
        Defines the multiplication operation against another `Quaternion` instance or
        against a scalar.
        """
        if isinstance(other, Quaternion):
            s1 = self.s
            x1 = self.i
            y1 = self.j
            z1 = self.k
            s2 = other.s
            x2 = other.i
            y2 = other.j
            z2 = other.k

            s = s1 * s2 - x1 * x2 - y1 * y2 - z1 * z2
            x = s1 * x2 + x1 * s2 + y1 * z2 - z1 * y2
            y = s1 * y2 - x1 * z2 + y1 * s2 + z1 * x2
            z = s1 * z2 + x1 * y2 - y1 * x2 + z1 * s2

            return Quaternion([x, y, z, s])
        if isinstance(other, Iterable):
            return self * Quaternion(other)
        if isinstance(other, (float, int)):
            return Quaternion(self.vector * other)

    def __rmul__(self, other: Quaternion | Iterable | float | int) -> Quaternion:
        """
        Defines the multiplication operation against another `Quaternion` instance or
        against a scalar.
        """
        if isinstance(other, Quaternion):
            s1 = other.s
            x1 = other.i
            y1 = other.j
            z1 = other.k
            s2 = self.s
            x2 = self.i
            y2 = self.j
            z2 = self.k

            s = s1 * s2 - x1 * x2 - y1 * y2 - z1 * z2
            x = s1 * x2 + x1 * s2 + y1 * z2 - z1 * y2
            y = s1 * y2 - x1 * z2 + y1 * s2 + z1 * x2
            z = s1 * z2 + x1 * y2 - y1 * x2 + z1 * s2

            return Quaternion(i=x, j=y, k=z, s=s)
        if isinstance(other, Iterable):
            return Quaternion(other) * self
        elif isinstance(other, (float, int)):
            return Quaternion(other * self.array)

    def as_rotation(self) -> Rotation:
        """
        Converts the quaternion to a scipy rotation object.

        Returns:
            (Rotation): Rotation object generated from quaterion.
        """
        return Rotation.from_quat(self.array)

    @classmethod
    def from_rotation(cls, r: Rotation) -> Quaternion:
        """
        Creates a `Quaternion` instance from a `Rotation` object.

        Returns:
            (Quaternion): New quaternion instance from `Rotation` object.
        """
        return cls(r.as_quat())


class Rotation(BaseModel):
    """
    Pydantic-compatible wrapper around scipy.spatial.transform.Rotation
    """

    # Store the quaternion values directly
    array: NDArray[Shape["4"], np.float64] = (0.0, 0.0, 0.0, 1.0)

    model_config = ConfigDict(
        frozen=True,
    )

    # Use properties to provide access to the ScipyRotation object
    @property
    def _rotation(self) -> ScipyRotation:
        """Get the underlying ScipyRotation object"""
        return ScipyRotation.from_quat(self.array)

    # Factory methods
    @classmethod
    def from_rotation(cls, rotation: ScipyRotation):
        """Create from ScipyRotation object"""
        return cls(array=rotation.as_quat())

    @classmethod
    def from_quat(cls, quat: Iterable[float]):
        """Create rotation from quaternion [x, y, z, w]"""
        return cls.from_rotation(rotation=ScipyRotation.from_quat(quat))

    @classmethod
    def from_euler(
        cls,
        seq: str,
        angles: tuple[float, float, float],
        degrees=False,
    ):
        """Create rotation from Euler angles"""
        return cls.from_rotation(
            ScipyRotation.from_euler(
                seq=seq,
                angles=angles,
                degrees=degrees,
            )
        )

    @classmethod
    def from_rotvec(
        cls,
        rotvec,
        degrees=False,
    ):
        """Create rotation from rotation vector"""
        return cls.from_rotation(
            ScipyRotation.from_rotvec(
                rotvec=rotvec,
                degrees=degrees,
            )
        )

    @classmethod
    def from_matrix(cls, matrix):
        """Create rotation from rotation matrix"""
        return cls.from_rotation(ScipyRotation.from_matrix(matrix))

    # Access methods
    def as_quat(self):
        """Return rotation as quaternion [x, y, z, w]"""
        return self._rotation.as_quat()

    def as_euler(self, seq: str, degrees: bool = False):
        """Return rotation as Euler angles"""
        return self._rotation.as_euler(seq, degrees)

    def as_rotvec(self):
        """Return rotation as rotation vector"""
        return self._rotation.as_rotvec()

    def as_matrix(self):
        """Return rotation as 3x3 matrix"""
        return self._rotation.as_matrix()

    @property
    def _constructor(self) -> Type[Self]:
        """Return the constructor for the class"""
        return type(self)

    # Operations
    def __mul__(self, other):
        """Compose rotations (right multiplication)"""
        if isinstance(other, Rotation):
            return self._constructor.from_rotation(self._rotation * other._rotation)
        if isinstance(other, ScipyRotation):
            return self._constructor.from_rotation(self._rotation * other)
        if isinstance(other, VectorR3):
            # Rotate vector
            rotated = self._rotation.apply(other.array)
            return other._constructor(rotated)
        if isinstance(other, (list, tuple, np.ndarray)):
            return self.__mul__(VectorR3(other))
        return NotImplemented

    def inv(self):
        """Return inverse rotation"""
        return self._constructor.from_rotation(self._rotation.inv())

    def magnitude(self):
        """Return the magnitude of the rotation in radians"""
        return self._rotation.magnitude()

    def mean(self, weights=None):
        """Compute the weighted mean of rotations"""
        return self._constructor.from_rotation(self._rotation.mean(weights))

    def reduce(self, left: Rotation = None, right: Rotation = None):
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
