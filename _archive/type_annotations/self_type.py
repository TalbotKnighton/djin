"""
Defines the `Self` type which needs to be imported different ways from different versions of 
Python.  I find it easier to do this once and then direct all of my other files to import from here.
"""
from __future__ import annotations

try:
    from typing import Self
except Exception:
    from typing_extensions import Self

__all__ = ['Self']
