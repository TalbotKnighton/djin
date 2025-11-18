from __future__ import annotations
from enum import StrEnum, auto
from typing import Callable, Optional, List, Union, Dict, Any
import numpy as np
from pydantic import field_validator, model_validator, ConfigDict, BaseModel
Number = float|int

__all__ = ['InertiaTensor', 'InertiaErrorType', 'InertiaErrorStrategy', 'ProductsOfInertiaSignConvention']

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

# First, let's define an enum for the types of errors that can occur
class InertiaErrorType(StrEnum):
    NEGATIVE_EIGENVALUES = auto()
    NON_REAL_EIGENVALUES = auto() 
    TRIANGLE_INEQUALITY_VIOLATION = auto()
    NON_SYMMETRIC = auto()

# Then, let's define an enum for the strategies to handle errors
class InertiaErrorStrategy(StrEnum):
    RAISE_EXCEPTION = auto()  # Default - just raise an exception
    CLIP_MAX_EIGENVALUE = auto()  # Fix triangle inequality by clipping max eigenvalue
    MAKE_POSITIVE_DEFINITE = auto()  # Replace negative eigenvalues with small positive values
    DISCARD_IMAGINARY_PARTS = auto()  # For non-real eigenvalues, discard imaginary parts
    SYMMETRIZE = auto()  # Make tensor symmetric by averaging corresponding elements

# Now, let's add this to your InertiaTensor class
class InertiaTensor(BaseModel):
    i_xx: Number
    i_yy: Number
    i_zz: Number
    i_xy: Number
    i_yz: Number
    i_zx: Number
    sign_convention: ProductsOfInertiaSignConvention
    
    # Define default error handling strategies
    error_handlers: Dict[InertiaErrorType, Union[InertiaErrorStrategy, Callable]] = {}
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
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
    
    @classmethod
    def create_with_validation(cls, 
                              i_xx: Number, 
                              i_yy: Number, 
                              i_zz: Number, 
                              i_xy: Number, 
                              i_yz: Number, 
                              i_zx: Number, 
                              sign_convention: ProductsOfInertiaSignConvention,
                              error_handlers: Optional[Dict[InertiaErrorType, Union[InertiaErrorStrategy, Callable]]] = None
                             ) -> 'InertiaTensor':
        """
        Create a new InertiaTensor with custom validation strategies.
        
        Args:
            i_xx, i_yy, i_zz: Moments of inertia
            i_xy, i_yz, i_zx: Products of inertia
            sign_convention: Convention for signs in the tensor
            error_handlers: Dictionary mapping error types to handling strategies
            
        Returns:
            InertiaTensor: Validated inertia tensor object
        """
        # Use empty dict if None provided
        if error_handlers is None:
            error_handlers = {}
            
        return cls(
            i_xx=i_xx,
            i_yy=i_yy,
            i_zz=i_zz,
            i_xy=i_xy,
            i_yz=i_yz,
            i_zx=i_zx,
            sign_convention=sign_convention,
            error_handlers=error_handlers
        )