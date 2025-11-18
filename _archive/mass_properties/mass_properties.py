"""
Defines MassProperties class and coordinate transformations
"""
from __future__ import annotations


# Standard package imports
Number = float|int
from enum import StrEnum, auto
import numpy as np
from typing import Callable, Dict, Optional, Type, Union

# Pydantic imports
from pydantic import BaseModel, ConfigDict, Field, model_validator, validate_call

# Local package imports
from djin.frames.frame import Frame, Point3D, GROUND_FRAME, Pose, Rotation, EuclideanVector
from djin.mass_properties.inertia_tensor import InertiaErrorStrategy, InertiaErrorType
from djin.type_annotations.spatial_types import Tensor3x3
from djin.type_annotations import Self
from djin.registry import default_registry

__all__ = ['ProductsOfInertiaSignConvention',  'InertiaTensor', 'CenterOfMass', 'MassProperties']

class ProductsOfInertiaSignConvention(StrEnum):
    """
    Flags signifying the two different mass properties product of inertia POI integral conventions

    Attributes:
        positive_integrals (str): indicates that the 
            POI values (i_xy, i_yx, i_xz, i_zx, i_yz, i_zy) will be negated in the inertia tensor.
        negative_integrals (str): indicates that the 
            POI values (i_xy, i_yx, i_xz, i_zx, i_yz, i_zy) 
            can be directly plugged into the inertia tensor.
    """
    positive_integrals = auto()
    negative_integrals = auto()

class InertiaTensor(BaseModel):
    """
    Internally represents the inertia tensor as the six nearly independent components (triangle rule must hold true)
    and allows the tensor to be built.

    Args:
        i_xx (Number): Moment of Inertia about x axis
        i_yy (Number): Moment of Inertia about y axis
        i_zz (Number): Moment of Inertia about z axis
        i_xy (Number): xy, yx Product of Inertia
        i_yz (Number): yz, zy Product of Inertia
        i_zx (Number): zx, xz Product of Inertia
        sign_convention (ProductsOfInertiaSignConvention): Determines whether or not
            POI values are to construct inertia tensor 
            (values will be negated when constructing the tensor if `sign_convention`
             is positive) 
    
    Attributes:
        i_xx (Number): Moment of Inertia about x axis
        i_yy (Number): Moment of Inertia about y axis
        i_zz (Number): Moment of Inertia about z axis
        i_xy (Number): xy, yx Product of Inertia
        i_yz (Number): yz, zy Product of Inertia
        i_zx (Number): zx, xz Product of Inertia
        i_yx (Number): xy, yx Product of Inertia
        i_zy (Number): yz, zy Product of Inertia
        i_xz (Number): zx, xz Product of Inertia
        sign_convention (ProductsOfInertiaSignConvention): Determines whether or not
            POI values are to construct inertia tensor 
            (values will be negated when constructing the tensor if `sign_convention`
             is positive) 
        tensor (Tensor3x3): 3x3 inertia tensor computed from given MOI and POI 
            including integral sign convention.
            If multiple uses are required in a given code scope, it is better to compute once
            and store in a variable for re-use.
        inverted_tensor (Tensor3x3): Inverted 3x3 inertia tensor computed via numpy.linalg.inv.
            If multiple uses are required in a given code scope, it is better to compute once
            and store in a variable for re-use.
        tensor_inverse (Tensor3x3): Inverted 3x3 inertia tensor computed via numpy.linalg.inv.
            Computation is performed every time this is called.
            If multiple uses are required in a given code scope, it is better to compute once
            and store in a variable for re-use.
    """
    i_xx: Number
    i_yy: Number
    i_zz: Number
    i_xy: Number
    i_yz: Number
    i_zx: Number
    sign_convention: ProductsOfInertiaSignConvention

    # Define default error handling strategies
    error_handlers: Dict[InertiaErrorType, Union[InertiaErrorStrategy, Callable]] = Field(
        exclude=True, 
        default_factory=lambda: {
            InertiaErrorType.NEGATIVE_EIGENVALUES: InertiaErrorStrategy.RAISE_EXCEPTION,
            InertiaErrorType.NON_REAL_EIGENVALUES: InertiaErrorStrategy.RAISE_EXCEPTION,
            InertiaErrorType.TRIANGLE_INEQUALITY_VIOLATION: InertiaErrorStrategy.RAISE_EXCEPTION,
            InertiaErrorType.NON_SYMMETRIC: InertiaErrorStrategy.RAISE_EXCEPTION,
        }
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def i_yx(self) -> Number:
        """
        Getter for i_yx,i_xy symmetric matrix component
        
        Returns:
            (Number): POI component
        """
        return self.i_xy
    
    @property
    def i_zy(self) -> Number:
        """
        Getter for i_zy,i_yz symmetric matrix component
        
        Returns:
            (Number): POI component
        """
        return self.i_yz
    
    @property
    def i_xz(self) -> Number:
        """
        Getter for i_xz,i_zx symmetric matrix component
        
        Returns:
            (Number): POI component
        """
        return self.i_zx

    @i_yx.setter
    def i_yx(self, value: Number):
        """
        Setter for i_yx,i_xy symmetric matrix component
        """
        self.i_xy = value
    
    @i_zy.setter
    def i_zy(self, value: Number):
        """
        Setter for i_yz,i_zy symmetric matrix component
        """
        self.i_yz = value
    
    @i_xz.setter
    def i_xz(self, value: Number):
        """
        Setter for i_xz,i_zx symmetric matrix component
        """
        self.i_zx = value

    @property
    def tensor(self) -> Tensor3x3:
        """
        Returns:
            (Tensor3x3): Computed inertia tensor from stored MOI and POI
        """
        c = -1 if self.sign_convention == ProductsOfInertiaSignConvention.positive_integrals else 1
        return np.array(
            [
                [  self.i_xx, c*self.i_xy, c*self.i_zx],
                [c*self.i_xy,   self.i_yy, c*self.i_yz],
                [c*self.i_zx, c*self.i_yz,   self.i_zz],
            ]
        )
    
    @model_validator(mode='after')
    def validate_inertia_tensor(self) -> InertiaTensor:
        """
        Validates that the inertia tensor is physically meaningful.
        
        Checks:
        1. Eigenvalues are real
        2. Eigenvalues are positive (positive-definite)
        3. Triangle inequality is obeyed
        4. Tensor is symmetric
        
        Depending on the error_handlers dictionary, different actions will be taken
        when validation fails.
        
        Returns:
            self: Returns the (potentially modified) tensor
        """
        # Apply default error handlers if not specified
        default_handlers = {
            InertiaErrorType.NEGATIVE_EIGENVALUES: InertiaErrorStrategy.RAISE_EXCEPTION,
            InertiaErrorType.NON_REAL_EIGENVALUES: InertiaErrorStrategy.RAISE_EXCEPTION,
            InertiaErrorType.TRIANGLE_INEQUALITY_VIOLATION: InertiaErrorStrategy.RAISE_EXCEPTION,
            InertiaErrorType.NON_SYMMETRIC: InertiaErrorStrategy.RAISE_EXCEPTION
        }
        
        # Merge with user-provided handlers, keeping user values for any overlapping keys
        all_handlers = {**default_handlers, **self.error_handlers}
        
        # Get the tensor to validate
        tensor = self.tensor
        
        # Check symmetry
        if not self.tensor_is_symmetric(tensor, tolerance=1e-5):
            self._handle_error(
                InertiaErrorType.NON_SYMMETRIC, 
                all_handlers, 
                tensor=tensor,
                message="Inertia tensor is not symmetric"
            )
        
        # Get eigenvalues and eigenvectors
        try:
            eig_vals, eig_vecs = np.linalg.eig(tensor)
        except Exception as e:
            raise ValueError(f"Failed to compute eigenvalues: {e}")
        
        # Check if eigenvalues are real
        if np.any(np.abs(np.imag(eig_vals)) > 1e-10):
            tensor = self._handle_error(
                InertiaErrorType.NON_REAL_EIGENVALUES, 
                all_handlers, 
                tensor=tensor, 
                eigenvalues=eig_vals,
                eigenvectors=eig_vecs,
                message="Inertia tensor has non-real eigenvalues"
            )
            # Recompute eigenvalues if tensor was modified
            eig_vals, eig_vecs = np.linalg.eig(tensor)
            
        # Check if eigenvalues are positive
        if np.any(np.real(eig_vals) < 0):
            tensor = self._handle_error(
                InertiaErrorType.NEGATIVE_EIGENVALUES, 
                all_handlers, 
                tensor=tensor, 
                eigenvalues=eig_vals,
                eigenvectors=eig_vecs,
                message="Inertia tensor has negative eigenvalues"
            )
            # Recompute eigenvalues if tensor was modified
            eig_vals, eig_vecs = np.linalg.eig(tensor)
        
        # Check triangle inequality
        real_eig_vals = np.real(eig_vals)
        max_idx = np.argmax(real_eig_vals)
        other_eigs_sum = np.sum(np.delete(real_eig_vals, max_idx))
        if real_eig_vals[max_idx] > other_eigs_sum + 1e-10:
            tensor = self._handle_error(
                InertiaErrorType.TRIANGLE_INEQUALITY_VIOLATION, 
                all_handlers, 
                tensor=tensor, 
                eigenvalues=eig_vals,
                eigenvectors=eig_vecs,
                message=f"Triangle inequality violated: max eigenvalue {real_eig_vals[max_idx]} > sum of others {other_eigs_sum}"
            )
        
        # If tensor was modified, update the object's values
        if not np.array_equal(tensor, self.tensor):
            self._update_from_tensor(tensor)
            
        return self
    
    def _handle_error(self, 
                     error_type: InertiaErrorType, 
                     handlers: Dict[InertiaErrorType, Union[InertiaErrorStrategy, Callable]],
                     tensor: np.ndarray,
                     message: str,
                     **kwargs) -> np.ndarray:
        """
        Handle an error according to the strategy defined for this error type.
        
        Args:
            error_type: The type of error that occurred
            handlers: Dictionary mapping error types to handling strategies
            tensor: The current tensor
            message: Error message to use if raising an exception
            **kwargs: Additional context about the error (e.g. eigenvalues)
            
        Returns:
            np.ndarray: The potentially modified tensor
        """
        handler = handlers.get(error_type)
        
        # If handler is a callable, call it with the tensor and kwargs
        if callable(handler):
            return handler(tensor=tensor, **kwargs)
        
        # Otherwise, handle based on the strategy enum
        if handler == InertiaErrorStrategy.RAISE_EXCEPTION:
            raise ValueError(message)
            
        elif handler == InertiaErrorStrategy.CLIP_MAX_EIGENVALUE:
            if error_type == InertiaErrorType.TRIANGLE_INEQUALITY_VIOLATION:
                return self.clip_max_eigenvalue_of_tensor(tensor)
            else:
                raise ValueError(f"Strategy {handler} not applicable for error type {error_type}")
                
        elif handler == InertiaErrorStrategy.MAKE_POSITIVE_DEFINITE:
            if error_type == InertiaErrorType.NEGATIVE_EIGENVALUES:
                return self._make_positive_definite(tensor, kwargs.get('eigenvalues'), kwargs.get('eigenvectors'))
            else:
                raise ValueError(f"Strategy {handler} not applicable for error type {error_type}")
                
        elif handler == InertiaErrorStrategy.DISCARD_IMAGINARY_PARTS:
            if error_type == InertiaErrorType.NON_REAL_EIGENVALUES:
                return self._discard_imaginary_parts(tensor)
            else:
                raise ValueError(f"Strategy {handler} not applicable for error type {error_type}")
                
        elif handler == InertiaErrorStrategy.SYMMETRIZE:
            if error_type == InertiaErrorType.NON_SYMMETRIC:
                return self._symmetrize_tensor(tensor)
            else:
                raise ValueError(f"Strategy {handler} not applicable for error type {error_type}")
        
        # If we get here, the handler wasn't recognized
        raise ValueError(f"Unknown error handling strategy: {handler}")
    
    def _update_from_tensor(self, tensor: np.ndarray) -> None:
        """Update the object's fields from a tensor"""
        c = -1 if self.sign_convention == ProductsOfInertiaSignConvention.positive_integrals else 1
        self.i_xx = tensor[0, 0]
        self.i_yy = tensor[1, 1]
        self.i_zz = tensor[2, 2]
        self.i_xy = c * tensor[0, 1]
        self.i_yz = c * tensor[1, 2]
        self.i_zx = c * tensor[0, 2]
    
    @staticmethod
    def _make_positive_definite(tensor: np.ndarray, eigenvalues: np.ndarray, eigenvectors: np.ndarray) -> np.ndarray:
        """
        Make tensor positive definite by replacing negative eigenvalues with small positive values.
        
        Args:
            tensor: Original tensor
            eigenvalues: Eigenvalues of the tensor
            eigenvectors: Eigenvectors of the tensor
            
        Returns:
            np.ndarray: Modified tensor with all positive eigenvalues
        """
        # Find the minimum positive eigenvalue to use as a reference
        pos_eigs = np.real(eigenvalues[np.real(eigenvalues) > 0])
        min_pos = np.min(pos_eigs) if len(pos_eigs) > 0 else 1e-6
        
        # Replace negative eigenvalues with a small positive value
        new_eigs = np.real(eigenvalues).copy()
        new_eigs[new_eigs <= 0] = min_pos * 1e-3
        
        # Reconstruct the tensor
        return eigenvectors @ np.diag(new_eigs) @ eigenvectors.T.conj()
    
    @staticmethod
    def _discard_imaginary_parts(tensor: np.ndarray) -> np.ndarray:
        """
        Discard imaginary parts of a tensor, ensuring the result is real and symmetric.
        
        Args:
            tensor: Original tensor
            
        Returns:
            np.ndarray: Real symmetric tensor
        """
        # Take the real part and ensure symmetry
        real_tensor = np.real(tensor)
        return (real_tensor + real_tensor.T) / 2
    
    @staticmethod
    def _symmetrize_tensor(tensor: np.ndarray) -> np.ndarray:
        """
        Make tensor symmetric by averaging corresponding off-diagonal elements.
        
        Args:
            tensor: Original tensor
            
        Returns:
            np.ndarray: Symmetric tensor
        """
        return (tensor + tensor.T) / 2
    
    @staticmethod
    def tensor_is_3x3(
            tensor: Tensor3x3
        ) -> bool:
        """
        Checks whether or not a tensor has shape 3x3.

        Args:
            tensor (Tensor3x3): Tensor for which the shape should be checked.

        Returns:
            (bool): `True` if shape of tensor is `3,3` else `False`
        """
        shape = np.array(tensor).shape
        return shape[0] == shape[1] == 3

    @staticmethod
    def tensor_is_symmetric(
            tensor: Tensor3x3,
            tolerance: Number = 1e-5,
        ) -> bool:
        """
        Asserts that tensor is symmetric to within the given tolerance.

        Args:
            tensor (Tensor3x3): A tensor.  Works for any tensor but is intented
                to be used for the special case of a 3x3 tensor.
            tolerance (Number): The threshold below which differences in the 
                symmetric matrix components will be considered to be negligible.
        
        Returns:
            (bool): `True` if tensor is elementwise symmetric to the given tolerance.
        """
        return np.allclose(np.array(tensor), np.array(tensor).transpose(), rtol=0, atol=tolerance)
    
    @staticmethod
    def get_tensor_3x3_eigenvalues_sorted_asserted_real_positive_semidefinite(
            tensor: Tensor3x3,
            eigen_value_real_rel_tolerance: Number = 1e-12
        ):
        """
        Asserts that the tensor has real eigenvalues and returns a sorted list.


        Args:
            tensor (Tensor3x3): A tensor for which the triangle inequality should be checked.
            eigen_value_real_rel_tolerance (Number): Used to check that eigenvalues are all real
        
        Returns:
            (List[int]): Sorted list of real eigenvalues
        """

        eig_vals, _ = np.linalg.eig(tensor)
        eig_vals_real = np.real(eig_vals)
        eig_vals_real_abs = np.abs(eig_vals_real)
        eig_vals_imag_abs = np.abs(np.imag(eig_vals))
        try:
            assert all((eig_vals_imag_abs / eig_vals_real_abs) < eigen_value_real_rel_tolerance)
        except AssertionError as e:
            raise ValueError(f'{eig_vals = } are not real')
        try:
            assert all(eig_vals_real > 0)
        except AssertionError as e:
            raise ValueError(f'{eig_vals = } are not positive semi-definite')
        eig_vals_real = list(eig_vals_real)
        eig_vals_real.sort()
        return eig_vals_real

    @classmethod
    def tensor_3x3_obeys_triangle_inequality(
            cls,
            tensor: Tensor3x3,
            eigen_value_real_tolerance: Number = 1e-12
        ) -> bool:
        """
        Checks whether or not the provided 3x3 tensor obeys the triangle inequality.
        Assumes all eigenvalues are positive semi-definit ane real.
        A generalized formulation is used to check that the greatest eigenvalue is
        not larger than the sum of the other eigenvalues.  
        This works in N dimensions with 3x3 being a special case.

        Args:
            tensor (Tensor3x3): A tensor for which the triangle inequality should be checked.
            eigen_value_real_tolerance (Number): Used to check that eigenvalues are all real
        
        Returns:
            (bool): `True` if tensor eigenvalues obey generalized triangle inequality
        """
        eig_vals = cls.get_tensor_3x3_eigenvalues_sorted_asserted_real_positive_semidefinite(
            tensor=tensor,
            eigen_value_real_rel_tolerance=eigen_value_real_tolerance
        )
        return np.sum(eig_vals[:-1]) + eigen_value_real_tolerance - eig_vals[-1] >= 0

    @classmethod
    def assert_inertia_tensor_is_physical(
            cls,
            tensor: Tensor3x3,
            relative_tolerance: Number,
        ):
        """
        Asserts that provided tensor is physical for mass properties inertia or 
        else raises a ValueError.  

        The tensor is asserted to meet the following conditions:
        
        - is 3x3
        - is elementwise symmetric to the given single element tolerance level
        - obeys the triangle inequality

        Args:
            tensor (Tensor3x3): tensor to evaluate
            relative_tolerance (Number): Tolerance against which each off-diagonal element pair
                is to be checked for symmetry.  
                Each pair-wise difference must be less than the given value.
        """
        tensor = np.array(tensor)
        try:
            assert cls.tensor_is_3x3(tensor=tensor)
        except AssertionError as e:
            raise ValueError(str(e) + '\n' + f'\n\t{tensor = }\n\t should be 3x3')
        
        eig_vals = cls.get_tensor_3x3_eigenvalues_sorted_asserted_real_positive_semidefinite(
            tensor=tensor,
            eigen_value_real_rel_tolerance=1e-5,
        )
        tolerance = relative_tolerance*np.min(eig_vals)
        try:
            assert cls.tensor_is_symmetric(tensor=tensor, tolerance=tolerance)
        except AssertionError as e:
            print (f'{eig_vals = }')
            raise ValueError(str(e) + '\n' + f'\n\t{tensor = }'
                             f'\n\tcomponents are not symmetric to within given {relative_tolerance = }.'
                             f'\n\t{tensor - tensor.transpose() = }')
        try:
            assert cls.tensor_3x3_obeys_triangle_inequality(
                tensor=tensor,
                eigen_value_real_tolerance=tolerance,
            )
        except AssertionError as e:
            from warnings import warn
            message = f'\n\t{tensor = } \nwith {eig_vals = } fails to meet triangle inequality'
            message += f'\n\tsince {np.sum(eig_vals[:-1]) + tolerance - eig_vals[-1] = } < 0.'
            warn(str(e) + '\n' + message)
            warn('Reducing max eigenvalue to produce physical tensor')

    @classmethod
    def clip_max_eigenvalue_of_tensor(
            cls,
            tensor: Tensor3x3,
            relative_tolerance: Number = 1e-5,
        ) -> Tensor3x3:
        """
        Clips the maximum eigenvalue of the tensor to be equal to the sum of the other eigenvalues
        plus a small tolerance.  This is done to ensure that the tensor is physical.
        
        Args:
            tensor (Tensor3x3): Tensor to clip.
            relative_tolerance (Number): Tolerance against which each off-diagonal element pair
                is to be checked for symmetry.  
                Each pair-wise difference must be less than the given value.
        
        Returns:
            (Tensor3x3): Clipped tensor.
        """
        eig_vals, eig_vecs = np.linalg.eig(tensor)
        i_max = np.argmax(eig_vals)
        max_possible = np.sum(np.delete(eig_vals, i_max))
        tolerance = relative_tolerance * np.min(eig_vals)
        eig_vals_clipped = np.clip(
            eig_vals,
            None, 
            max_possible - tolerance,
        )
        return eig_vecs @ np.diag(eig_vals_clipped) @ eig_vecs.T
    
    def clip_max_eigenvalue(self):
        """
        Clips the maximum eigenvalue of the tensor to be equal to the sum of the other eigenvalues
        plus a small tolerance.  This is done to ensure that the tensor is physical.
        
        Returns:
            (Tensor3x3): Clipped tensor.
        """
        clipped_tensor = type(self).clip_max_eigenvalue_of_tensor(
            tensor=self.tensor,
            relative_tolerance=1e-5,
        )
        return type(self).from_tensor(
            tensor=clipped_tensor,
            sign_convention=self.sign_convention,
        )
    
    @classmethod
    def from_tensor(
            cls, 
            tensor: Tensor3x3, 
            sign_convention: ProductsOfInertiaSignConvention,
            relative_symmetry_tolerance: Number = 1e-5,
        ) -> InertiaTensor:
        """
        Returns a new `InertiaTensor` object based on the provided inertia tensor.
        The tensor is checked for physical meaningfulness.
        
        That is, the tensor is checked to be 3x3, symmetric, and obey the triangle inequality

        Args:
            tensor (Tensor3x3): Inertia tensor from which the `InertiaTensor` object is to be created.
                Triangle inequality and symmetry checks are performed 
                to ensure that the provided tensor is physically meaningful.
            sign_convention (ProductsOfInertiaSignConvention): Sign convention to be used for the new
                `InertiaTensor` object.  It is assumed that the provided `tensor` argument is physical
                (i.e. that it includes the negative sign in the off-diagonal POI terms).
            relative_symmetry_tolerance (Number): A symmetry check is performed to ensure that
                the tensor is valid. The `relative_symmetry_tolerance` sets the threshold below which
                differences in symmetric POI will be considered to be negligible.
                Absolute tolerance will be `relative_symmetry_tolerance` times the minimum
                eigenvalue of the matrix.

        Returns:
            (InertiaTensor): New `InertiaTensor` instance from given tensor.
                Checks that tensor is symmetric within given tolerance.
        """
        cls.assert_inertia_tensor_is_physical(
            tensor=tensor, 
            relative_tolerance=relative_symmetry_tolerance)
        c = -1 if sign_convention == ProductsOfInertiaSignConvention.positive_integrals else 1
        return cls(
            i_xx=tensor[0, 0],
            i_yy=tensor[1, 1],
            i_zz=tensor[2, 2],
            i_xy=c*tensor[0, 1],
            i_yz=c*tensor[1, 2],
            i_zx=c*tensor[0, 2],
            sign_convention=sign_convention,
        )
    
    def change_frame(self, old_frame: Frame, new_frame: Frame, mass: Number) -> Self:
        """
        Returns a new instance of `InertiaTensor` expressed the given `new_frame`.
        Uses frame transformations of the `Frame` class 
        as well as the parallel axis theorem to calculate new tensor components.
        Integral sign convention is preserved.

        Args:
            old_frame (Frame): Reference `Frame` in which the inertia tensor is presently defined
            new_frame (Frame): Reference `Frame` to which the inertia tensor should be converted
            mass (Number): Mass to be used for the parallel axis theorem contribution to the 
                (in the most general case) rotated and shifted inertia tensor.
        """
        # express the old_frame relative to the new_frame
        f = old_frame.change_parent_frame(new_frame)
        # calculate the parallel axis theorem term in the new_frame
        x, y, z = tuple(f.pose.position.as_array())
        parallel_axis_term_in_new_frame = mass * np.array(  # calculated in 
            [
                [(y**2 + z**2), -x*y, -x*z],
                [-y*x, (x**2 + z**2), -y*z],
                [-z*x, -z*y, (x**2 + y**2)],
            ]
        )
        # rotate inertia tensor into the new_frame coordinates
        rotated_tensor = f.pose.rotation.as_matrix() @ self.tensor @ f.pose.rotation.inv().as_matrix()
        # caluclated the combined tensor relative to the new_frame
        new_tensor = rotated_tensor + parallel_axis_term_in_new_frame
        # construct a new `InertiaTensor` instance and return it
        _constructor = type(self)
        return _constructor.from_tensor(
            tensor=new_tensor,
            sign_convention=self.sign_convention,
        )

    def flip_sign_convention(self, inplace=True) -> InertiaTensor:
        """
        Returns an `InertiaTensor` object with opposite POI integral convention.

        If `inplace==True` the internal memory of the existing instance is changed.
        If `inplace==False`, a new `InteriaTensor` object is returned.

        This method can be useful for comparing mass properties 
        between different codes that may use different conventions.

        Args:
            inplace (bool): Determines whether the existing object data is changed or if
                a new instance is created and returned.

        Returns:
            (InertiaTensor): Inertia tensor with flipped integral convention.
                Returns a reference to the existing instance if `inplace==True` 
                else returns a new instance.
        """
        if inplace:
            match self.sign_convention:
                case ProductsOfInertiaSignConvention.positive_integrals:
                    self.sign_convention = ProductsOfInertiaSignConvention.negative_integrals
                case ProductsOfInertiaSignConvention.negative_integrals:
                    self.sign_convention = ProductsOfInertiaSignConvention.positive_integrals
            self.i_xy = - self.i_xy
            self.i_yz = - self.i_yz
            self.i_zx = - self.i_zx
            return self
        else:
            _constructor = type(self)
            match self.sign_convention:
                case ProductsOfInertiaSignConvention.positive_integrals:
                    return _constructor(
                        i_xx=self.i_xx,
                        i_yy=self.i_yy,
                        i_zz=self.i_zz,
                        i_xy=self.i_xy,
                        i_yz=self.i_yz,
                        i_zx=self.i_zx,
                        sign_convention=ProductsOfInertiaSignConvention.negative_integrals,
                    )
                case ProductsOfInertiaSignConvention.negative_integrals:
                    return _constructor(
                        i_xx=self.i_xx,
                        i_yy=self.i_yy,
                        i_zz=self.i_zz,
                        i_xy=self.i_xy,
                        i_yz=self.i_yz,
                        i_zx=self.i_zx,
                        sign_convention=ProductsOfInertiaSignConvention.positive_integrals,
                    )

    @property
    def tensor_inverse(self) -> Tensor3x3:
        r"""
        Computes the inverse inertia tensor via np.linalg.inv

        Computation is performed every time this is called. 
        So, if multiple calls are needed in the same scope,
        it will be better to store the inverted tensor as a variable for re-use.

        Returns:
            (Tensor3x3): Inverted inertia tensor.  Use this in dyanmics equations such as:
                $\vec{\alpha} = I^{-1}\vec{\tau}$ where $\vec{\alpha}$ is angular acceleration,
                $\vec{\tau}$ is torque, and $I$ is the inertia tensor.
        """
        return np.linalg.inv(self.tensor)

class CenterOfMass(BaseModel):
    """
    Center of mass consists of two attributes: mass and position.
    Frame transformations are handled by the position `Point3D3D` object.

    Args:
        mass (Number): Point mass
        position (Point3D): Position of the point mass.  The `Point3D3D`
            object handles frame transformations via the `Frame` class.

    """
    mass: Number
    position: Point3D
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def change_frame(self, new_frame: Frame) -> Type[Self]:
        """
        Args:
            new_frame (Frame): Frame to which the position of the newly created CenterOfMass
                instance will be referenced.

        Returns:
            (Type[Self]): Returns a new instance of `CenterOfMass` (or a child thereof)
                with new `position` defined in given `new_frame`.
        """
        _constructor = type(self)
        return _constructor(
            mass = self.mass,
            position = self.position.change_frame(new_frame),
        )

    @property
    def _constructor(self):
        return type(self)
    
    def __add__(self, other: CenterOfMass):
        """
        Adds two `CenterOfMass` objects together.  The mass is summed and the position
        is averaged based on the mass of each object.

        Args:
            other (CenterOfMass): `CenterOfMass` object to add to this one.

        Returns:
            (CenterOfMass): New `CenterOfMass` object with summed mass and averaged position.
        """
        try:
            assert isinstance(other, CenterOfMass)
        except AssertionError as e: 
            raise ValueError('Can only add/subtract from CenterOfMass objects') from e
        
        total_mass = self.mass + other.mass
        try:
            assert total_mass > 0
        except AssertionError as e:
            raise ValueError('Cannot subtract from a zero mass object') from e
        
        new_position = (self.position * self.mass + other.position * other.mass) / total_mass
        return self._constructor(mass=total_mass, position=new_position)
    
    def __sub__(self, other: CenterOfMass):
        """
        Subtracts two `CenterOfMass` objects.  The mass is summed and the position
        is averaged based on the mass of each object.
        Args:
            other (CenterOfMass): `CenterOfMass` object to subtract from this one.
        Returns:
            (CenterOfMass): New `CenterOfMass` object with summed mass and averaged position.
        """
        try:
            assert isinstance(other, CenterOfMass)
        except AssertionError as e: 
            raise ValueError('Can only add/subtract from CenterOfMass objects') from e
        
        total_mass = self.mass - other.mass
        try:
            assert total_mass > 0
        except AssertionError as e:
            raise ValueError('Cannot subtract from a zero mass object') from e
        
        new_position = (self.position * self.mass - other.position * other.mass) / total_mass
        return self._constructor(mass=total_mass, position=new_position)
    
    def __radd__(self, other: CenterOfMass):
        """
        Adds two `CenterOfMass` objects together.  The mass is summed and the position
        is averaged based on the mass of each object.
        Args:
            other (CenterOfMass): `CenterOfMass` object to add to this one.
        Returns:
            (CenterOfMass): New `CenterOfMass` object with summed mass and averaged position.
        """
        try:
            assert isinstance(other, CenterOfMass)
        except AssertionError as e: 
            raise ValueError('Can only add/subtract from CenterOfMass objects') from e
        
        total_mass = self.mass + other.mass
        try:
            assert total_mass > 0
        except AssertionError as e:
            raise ValueError('Cannot subtract from a zero mass object') from e
        # Calculate the new position based on the weighted average
        # of the two center of mass positions
        # The new position is the weighted average of the two positions
        # based on their respective masses
        # The formula is: new_position = (m1 * p1 + m2 * p2) / (m1 + m2)
        # where m1 and m2 are the masses and p1 and p2 are the positions
        # of the two center of mass objects
        new_position = (self.position * self.mass + other.position * other.mass) / total_mass
        return self._constructor(mass=total_mass, position=new_position)
    
    def __rsub__(self, other: CenterOfMass):
        """
        Subtracts two `CenterOfMass` objects.  The mass is summed and the position
        is averaged based on the mass of each object.
        Args:
            other (CenterOfMass): `CenterOfMass` object to subtract from this one.
        Returns:
            (CenterOfMass): New `CenterOfMass` object with summed mass and averaged position.
        """
        try:
            assert isinstance(other, CenterOfMass)
        except AssertionError as e: 
            raise ValueError('Can only add/subtract from CenterOfMass objects') from e
        
        total_mass = other.mass - self.mass
        try:
            assert total_mass > 0
        except AssertionError as e:
            raise ValueError('Cannot subtract from a zero mass object') from e
        
        new_position = (other.position * other.mass - self.position * self.mass) / total_mass
        return self._constructor(mass=total_mass, position=new_position)
    

    
class MassProperties(BaseModel):
    """
    It is possible to write the equations of motion in an inertial frame such that
    the linear and rotational dynamics are decoupled for independent rigid bodies
    (see Landau and Lifshits for a concise proof).
    `MassProperties` are defined as a `CenterOfMass` describing the point mass
    needed for linear dynamics and an `InertiaTensor` needed for rotational dynamics.
    The necessary frame transformations are encoded into these separate object defentions.
    
    Attributes:
        center_of_mass (CenterOfMass): `CenterOfMass` object describing a point mass at a particular location in a given reference frame.
        inertia_tensor (InertiaTensor): `InertiaTensor` object describing the 3x3 tensor in a given reference frame.
            The inertia tensor is assumed to be given in the `center_of_mass` position reference frame.
            The CoM position reference frame will be used as the starting point for `MassProperties` frame transformations.
        frame (Frame): center_of_mass reference frame.
    """
    center_of_mass: CenterOfMass
    inertia_tensor: InertiaTensor

    model_config = ConfigDict(arbitrary_types_allowed=True)


    @property
    def _constructor(self) -> Type[Self]:
        return type(self)
    
    @property
    def frame(self) -> Frame:
        """
        Returns:
            (Frame): reference frame for center of mass position.
                The inertia tensor associated with the `MassProperties` class is
                assumed to be defined in the same frame as the center of mass position frame.
        """
        return self.center_of_mass.position.frame

    @classmethod
    def from_components(
        cls,
        mass: Number,
        cm_x: Number,
        cm_y: Number,
        cm_z: Number,
        i_xx: Number,
        i_yy: Number,
        i_zz: Number,
        i_xy: Number,
        i_yz: Number,
        i_zx: Number, 
        frame: Frame,
        sign_convention: ProductsOfInertiaSignConvention = ProductsOfInertiaSignConvention.positive_integrals,
    ) -> MassProperties:
        """
        Returns a new `MassProperties` object from given inputs.

        Args:
            mass (Number): point mass
            cm_x (Number): x position of point mass in given `frame`
            cm_y (Number): y position of point mass in given `frame`
            cm_z (Number): z position of point mass in given `frame`
            i_xx (Number): xx MOI of inertia tensor in given `frame`
            i_yy (Number): yy MOI of inertia tensor in given `frame`
            i_zz (Number): zz MOI of inertia tensor in given `frame`
            i_xy (Number): xy POI of inertia tensor in given `frame`
            i_yz (Number): yz POI of inertia tensor in given `frame` 
            i_zx (Number): zx POI of inertia tensor in given `frame`
            frame (Frame): Reference frame for given point mass and inertia tensor
            sign_convention (ProductsOfInertiaSignConvention): Inetgral sign convention
                determining how the inertia tensor is constructed from the given POI.
                Use positive sign convention if POI need to be negated when constructing the 
                physical inertia tensor.         
        
        Returns:
            (MassProperties): New `MassProperties` object from given components in given `Frame`.
        """
        return cls(
            center_of_mass = CenterOfMass(
                mass = mass,
                position = Point3D.from_components(
                    x=cm_x, 
                    y=cm_y, 
                    z=cm_z, 
                    frame=frame,
                ),
            ),
            inertia_tensor = InertiaTensor(
                i_xx = i_xx,
                i_yy = i_yy,
                i_zz = i_zz,
                i_xy = i_xy,
                i_yz = i_yz,
                i_zx = i_zx,
                sign_convention = sign_convention,
            )
        )
    
    def change_frame(self, new_frame: Frame) -> Type[Self]:
        """
        Returns a new instance of `MassProperties` (or child thereof) relative to `new_frame`.
        Frame conversions are defined in the `CenterOfMass` and `InertiaTensor` class definitions
        (and recursively in the `Point3D3D` and `Frame` classes that they reference).

        Args:
            new_frame (Frame): Reference frame in which the new `MassProperties`
                instance should be expressed.
        
        Returns:
            (MassProperties): New instance of `MassProperties` (or child thereof) expressed
                relative to `new_frame`.  The stored `CenterOfMass` and `InertiaTensor`
                references will also be new objects as returned by the respective `change_frame`
                methods of those classes.
        """
        new_center_of_mass = self.center_of_mass.change_frame(
            new_frame=new_frame
        )
        new_inertia_tensor = self.inertia_tensor.change_frame(
            old_frame=self.frame, 
            new_frame=new_frame, 
            mass=self.center_of_mass.mass
        )
        _constructor = type(self)
        return _constructor(
            center_of_mass=new_center_of_mass,
            inertia_tensor=new_inertia_tensor,
        )
    
    def in_global_frame(self) -> Type[Self]:
        """
        Uses the `MassProperties.change_frame' method with a `GROUND_FRAME` input
        to compute the mass properties in the ground frame.

        Returns:
            (MassProperties): A new mass properties object with values expressed in the 
                `GROUND_FRAME` (i.e. global inertial reference frame).
        """
        return self.change_frame(GROUND_FRAME)

    def __add__(self, other: MassProperties):
        new_com = self.center_of_mass + other.center_of_mass
        new_frame = new_com.position.get_new_frame_at_point()
        i_self = self.inertia_tensor.change_frame(
            old_frame=self.frame, 
            new_frame=new_frame,
            mass=self.center_of_mass.mass,
        )
        i_other = other.inertia_tensor.change_frame(
            old_frame=other.frame,
            new_frame=new_frame,
            mass=other.center_of_mass.mass,
        )
        raise self._constructor(
            center_of_mass = new_com,
            inertia_tensor = i_self + i_other,
        )
    
    def __radd__(self, other: MassProperties):
        new_com = other.center_of_mass + self.center_of_mass
        new_frame = new_com.position.get_new_frame_at_point()
        i_other = other.inertia_tensor.change_frame(
            old_frame=other.frame,
            new_frame=new_frame,
            mass=other.center_of_mass.mass,
        )
        i_self = self.inertia_tensor.change_frame(
            old_frame=self.frame, 
            new_frame=new_frame,
            mass=self.center_of_mass.mass,
        )
        raise self._constructor(
            center_of_mass = new_com,
            inertia_tensor = i_other + i_self,
        )
    
    def __sub__(self, other: MassProperties):
        new_com = self.center_of_mass - other.center_of_mass
        new_frame = new_com.position.get_new_frame_at_point()
        i_self = self.inertia_tensor.change_frame(
            old_frame=self.frame, 
            new_frame=new_frame,
            mass=self.center_of_mass.mass,
        )
        i_other = other.inertia_tensor.change_frame(
            old_frame=other.frame,
            new_frame=new_frame,
            mass=other.center_of_mass.mass,
        )
        raise self._constructor(
            center_of_mass = new_com,
            inertia_tensor = i_self - i_other,
        )

    def __rsub__(self, other: MassProperties):  
        new_com = other.center_of_mass - self.center_of_mass
        new_frame = new_com.position.get_new_frame_at_point()
        i_other = other.inertia_tensor.change_frame(
            old_frame=other.frame,
            new_frame=new_frame,
            mass=other.center_of_mass.mass,
        )
        i_self = self.inertia_tensor.change_frame(
            old_frame=self.frame, 
            new_frame=new_frame,
            mass=self.center_of_mass.mass,
        )
        raise self._constructor(
            center_of_mass = new_com,
            inertia_tensor = i_other - i_self,
        )

def main():
    """Run some tests here"""
    fa = Frame.from_components(
        position=EuclideanVector(x=0, y=0, z=0),
        rotation=Rotation.from_euler(seq='ZXZ', angles=(0, 0, 0), degrees=True),
        parent=GROUND_FRAME,
    )
    fb = Frame.from_components(
        position=EuclideanVector(x=0, y=0, z=0),
        rotation=Rotation.from_euler(seq='ZXZ', angles=(0, 0, 0), degrees=True),
        parent=GROUND_FRAME,
    )
    cma = CenterOfMass(
        mass=5.0,
        position=Point3D.from_components(x=1, y=0, z=0, frame=fa)
    )
    cmb = CenterOfMass(
        mass=5.0,
        position=Point3D.from_components(x=1.0, y=0, z=0, frame=fb)
    )
    cmc = (cma+cmb)
    print(cma+cmb)
    print(default_registry.model_dump_json(indent=2))
    
if __name__ == '__main__':
    """Run some tests here"""
    main()
