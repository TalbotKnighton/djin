from typing import Union, overload


# Define overloaded function signatures
@overload
def get_value(use_string: bool, value: int) -> str: ...


@overload
def get_value(use_string: bool, value: int) -> int: ...


# Actual implementation
def get_value(use_string: bool, value: int) -> Union[str, int]:
    if use_string:
        return str(value)
    else:
        return value


# Now the type checker knows the return type based on the first parameter
str_val = get_value(True, 42)  # Type: str
int_val = get_value(False, 42)  # Type: int
