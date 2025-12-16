from __future__ import annotations
from typing import Annotated, Any, Iterable, Optional, Self, Type, TypeAlias

from numpydantic import NDArray
import numpy as np
from scipy.spatial.transform import Rotation as ScipyRotation
from djin.base import pydantic as pyd, immutable

# https://github.com/p2p-ld/numpydantic/issues/41
NDArrayFloat64: TypeAlias = Annotated[
    np.ndarray[Any, np.dtype[np.float64]],
    pyd.GetPydanticSchema(
        lambda tp, handler: NDArray[Any, np.float64].__get_pydantic_core_schema__(  # type: ignore
            NDArray[Any, np.float64], handler
        )
    ),
]


@immutable
class VectorR3(pyd.BaseModel):
    model_config = pyd.ConfigDict(extra="forbid")

    # Define a 1D array of length 3 with float64 dtype
    data: tuple[float, float, float] = (0, 0, 0)

    def all_close(self, other: VectorR3 | NDArrayFloat64 | Iterable[float]) -> bool:
        return np.allclose(self.array, np.array(other))

    @classmethod
    def from_array(cls, array: NDArrayFloat64) -> Self:
        """
        Creates a new `VectorR3` instance from a 3x3 numpy array.

        Returns:
            (VectorR3): New `VectorR3` instance.
        """
        return cls(data=array.tolist())

    @property
    def array(self) -> NDArrayFloat64:
        return np.asarray(self.data)

    # @pyd.field_validator("tuple")
    # def validate_array(cls, v: tuple[float, float, float]) -> NDArrayFloat64:
    #     """
    #     Validates that the input array is of shape (3,).
    #     """
    #     arr = np.asarray(v, dtype=np.float64)
    #     if arr.shape != (3,):
    #         raise ValueError(f"Array must be of shape (3,), got {arr.shape}")
    #     return arr

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

    def __array__(self, *args, **kwargs) -> np.ndarray:
        return self.array.__array__(*args, **kwargs)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        """
        Handle numpy ufuncs.
        """
        arrays = []
        for input_ in inputs:
            if isinstance(input_, VectorR3):
                arrays.append(input_.array)
            else:
                arrays.append(input_)
        result = getattr(ufunc, method)(*arrays, **kwargs)
        if isinstance(result, np.ndarray) and result.shape == (3,):
            return self._constructor.from_array(array=result)
        return result

    # def __iter__(self) -> Iterable[float]:
    #     return iter(self.array)

    def __neg__(self) -> VectorR3:
        return self._constructor.from_array(array=-self.array)

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
            data=np.array(
                [
                    x,
                    y,
                    z,
                ]
            ).tolist()
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
        return cls(data=(0, 0, 0))

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
            return self._constructor.from_array(array=self.array + other.array)
        if isinstance(other, (float, int)):
            return self._constructor.from_array(array=self.array + other)
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
            return self._constructor.from_array(array=self.array * other)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __rmul__(self, other: float | int) -> VectorR3:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return self._constructor.from_array(array=other * self.array)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __truediv__(self, other: float | int) -> VectorR3:
        """
        Defines the division operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return self._constructor.from_array(array=self.array / other)
        raise TypeError(
            f"Unsupported type for division: {type(other)}. Expected float or int."
        )


@immutable
class Tensor3x3(pyd.BaseModel):
    model_config = pyd.ConfigDict(extra="forbid")

    # Define a 2D array of shape (3, 3) with float64 dtype
    data: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ] = np.eye(3).tolist()

    @property
    def array(self) -> NDArrayFloat64:
        return np.asarray(self.data)

    @classmethod
    def from_array(cls, array: NDArrayFloat64) -> Self:
        """
        Creates a new `Tensor3x3` instance from a 3x3 numpy array.

        Returns:
            (Tensor3x3): New `Tensor3x3` instance.
        """
        return cls(data=array.tolist())

    def __add__(self, other: float | int | Tensor3x3) -> Tensor3x3:
        """
        Defines the addition operation against another `Tensor3x3` instance.
        """
        if isinstance(other, Tensor3x3):
            return self._constructor.from_array(array=self.array + other.array)
        if isinstance(other, (float, int)):
            return self._constructor.from_array(array=self.array + other)
        raise TypeError(
            f"Unsupported type for addition: {type(other)}. Expected Tensor3x3."
        )

    def __radd__(self, other: float | int | Tensor3x3) -> Tensor3x3:
        """
        Defines the addition operation against another `Tensor3x3` instance.
        """
        if isinstance(other, Tensor3x3):
            return Tensor3x3.from_array(array=other.array + self.array)
        if isinstance(other, (float, int)):
            return Tensor3x3.from_array(array=other + self.array)
        raise TypeError(
            f"Unsupported type for addition: {type(other)}. Expected Tensor3x3."
        )

    def __mul__(self, other: float | int) -> Tensor3x3:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return Tensor3x3.from_array(array=self.array * other)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __rmul__(self, other: float | int) -> Tensor3x3:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return Tensor3x3.from_array(array=other * self.array)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    @property
    def _constructor(self) -> Type[Tensor3x3]:
        """
        Returns the constructor for the class. This is used to create new instances of the class.
        """
        return type(self)


@immutable
class Tensor3x3Symmetric(pyd.BaseModel):
    model_config = pyd.ConfigDict(extra="forbid")

    xx: float
    yy: float
    zz: float
    xy: float
    zx: float
    yz: float

    @property
    def yx(self) -> float:
        return self.xy

    @property
    def xz(self) -> float:
        return self.zx

    @property
    def zy(self) -> float:
        return self.yz

    @property
    def array(self) -> NDArrayFloat64:
        return np.asarray(
            [
                [self.xx, self.xy, self.xz],
                [self.yx, self.yy, self.yz],
                [self.zx, self.yz, self.zz],
            ]
        )

    @classmethod
    def from_array(
        cls,
        array: NDArrayFloat64,
    ) -> Self:
        """
        Creates a new `Tensor3x3Symmetric` instance from a 3x3 numpy array.

        Returns:
            (Tensor3x3Symmetric): New `Tensor3x3Symmetric` instance.
        """
        # TODO verify all close
        return cls(
            xx=array[0, 0],
            yy=array[1, 1],
            zz=array[2, 2],
            xy=array[0, 1],
            zx=array[2, 0],
            yz=array[1, 2],
        )

    def __add__(self, other: float | int | Tensor3x3Symmetric) -> Tensor3x3Symmetric:
        """
        Defines the addition operation against another `Tensor3x3` instance.
        """
        if isinstance(other, Tensor3x3Symmetric):
            return self._constructor.from_array(array=self.array + other.array)
        if isinstance(other, (float, int)):
            return self._constructor.from_array(array=self.array + other)
        raise TypeError(
            f"Unsupported type for addition: {type(other)}. Expected Tensor3x3."
        )

    def __radd__(self, other: float | int | Tensor3x3Symmetric) -> Tensor3x3Symmetric:
        """
        Defines the addition operation against another `Tensor3x3` instance.
        """
        if isinstance(other, Tensor3x3Symmetric):
            return Tensor3x3Symmetric.from_array(array=other.array + self.array)
        if isinstance(other, (float, int)):
            return Tensor3x3Symmetric.from_array(array=other + self.array)
        raise TypeError(
            f"Unsupported type for addition: {type(other)}. Expected Tensor3x3."
        )

    def __mul__(self, other: float | int) -> Tensor3x3Symmetric:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return Tensor3x3Symmetric.from_array(array=self.array * other)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    def __rmul__(self, other: float | int) -> Tensor3x3Symmetric:
        """
        Defines the multiplication operation against a scalar.
        """
        if isinstance(other, (float, int)):
            return Tensor3x3Symmetric.from_array(array=other * self.array)
        raise TypeError(
            f"Unsupported type for multiplication: {type(other)}. Expected float or int."
        )

    @property
    def _constructor(self) -> Type[Tensor3x3Symmetric]:
        """
        Returns the constructor for the class. This is used to create new instances of the class.
        """
        return type(self)


@immutable
class Quaternion(pyd.BaseModel):
    model_config = pyd.ConfigDict(extra="forbid")

    # Define a 1D array of length 4 with float64 dtype
    data: tuple[float, float, float, float] = (0, 0, 0, 1)

    def norm(self) -> float:
        return np.sqrt(np.sum((self * self).array))

    def conj(self):
        return Quaternion(
            data=(
                -self.data[0],
                -self.data[1],
                -self.data[2],
                self.data[3],
            )
        )

    def inv(self) -> Quaternion:
        return self.conj() * (self.norm() ** 2)

    @property
    def array(self) -> NDArrayFloat64:
        return np.asarray(self.data)

    @classmethod
    def from_array(cls, array: NDArrayFloat64) -> Self:
        """
        Creates a new `Quaternion` instance from a length 4 numpy array.

        Returns:
            (Quaternion): New `Quaternion` instance.
        """
        return cls(data=array.tolist())

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
        return VectorR3.from_array(array=self.array[:3])

    @property
    def scalar(self):
        return self.array[3]

    @classmethod
    def from_components(
        cls,
        vector: VectorR3,
        scalar: float | int,
    ) -> Quaternion:
        """
        Creates a new `Quaternion` instance from a vector and scalar.
        Asserts vector is length 3

        Returns:
            (Quaternion): New quaternion object.
        """
        return cls.from_array(array=np.array(list(vector) + [scalar]))

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

            return Quaternion.from_array(array=np.array([x, y, z, s]))
        if isinstance(other, Iterable):
            return self * Quaternion.from_array(array=np.array(other))
        if isinstance(other, (float, int)):
            return Quaternion.from_array(array=np.array(self.array * other))

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

            return Quaternion.from_components(
                vector=VectorR3.from_array(array=np.array([x, y, z])),
                scalar=s,
            )
        if isinstance(other, Iterable):
            return Quaternion.from_array(array=np.array(other)) * self
        elif isinstance(other, (float, int)):
            return Quaternion.from_array(array=np.array(other * self.array))

    def as_rotation(self) -> Rotation:
        """
        Converts the quaternion to a scipy rotation object.

        Returns:
            (Rotation): Rotation object generated from quaterion.
        """
        return Rotation.from_quat(self.array)

    @classmethod
    def from_rotation(cls, r: Rotation | ScipyRotation) -> Quaternion:
        """
        Creates a `Quaternion` instance from a `Rotation` object.

        Returns:
            (Quaternion): New quaternion instance from `Rotation` object.
        """
        return cls.from_array(array=r.as_quat())

    def __neg__(self):
        return type(self).from_array(array=-self.array)


@immutable
class Rotation(pyd.BaseModel):
    """
    Pydantic-compatible wrapper around scipy.spatial.transform.Rotation
    """

    # Store the quaternion values directly
    data: tuple[float, float, float, float] = (0, 0, 0, 1)

    @property
    def array(self) -> NDArrayFloat64:
        return np.asarray(self.data)

    @classmethod
    def from_array(cls, array: NDArrayFloat64) -> Self:
        """
        Creates a new `Rotation` instance from a length 4 numpy array.

        Returns:
            (Rotation): New `Rotation` instance.
        """
        return cls(data=array.tolist())

    # Use properties to provide access to the ScipyRotation object
    @property
    def _rotation(self) -> ScipyRotation:
        """Get the underlying ScipyRotation object"""
        return ScipyRotation.from_quat(self.array)

    # Factory methods
    @classmethod
    def from_rotation(cls, rotation: ScipyRotation):
        """Create from ScipyRotation object"""
        return cls.from_array(array=rotation.as_quat())

    @classmethod
    def from_quat(cls, quat: Iterable[float]):
        """Create rotation from quaternion [x, y, z, w]"""
        return cls.from_rotation(rotation=ScipyRotation.from_quat(np.array(quat)))

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
        return self._rotation.as_euler(seq, degrees)  # type: ignore

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
            return other._constructor.from_array(array=rotated)
        if isinstance(other, (list, tuple, np.ndarray)):
            return self.__mul__(VectorR3.from_array(array=np.array(other)))
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

    def reduce(
        self,
        left: Optional[Rotation] = None,
        right: Optional[Rotation] = None,
    ):
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


def _type():
    print(VectorR3.from_array(array=np.array([1.0, 2.0, 3.0])))
    print(Tensor3x3.from_array(array=np.eye(3)))
    x = (
        Quaternion.from_array(array=np.array([0, 1, 0, 0]))
        * Quaternion(data=(0, 0, 0, 1))
        * Quaternion.from_array(array=np.array([0, 1, 0, 0]))
    )
    print(x)


if __name__ == "__main__":
    _type()
