import djin.mass_properties as mp

# Create in memory
inertia_tensor = mp.InertiaTensor(
    xx=1,
    yy=1,
    zz=1,
    xy=0.1,
    zx=0.1,
    yz=0.1,
    integral_convention=mp.IntegralConvention.positive,
)
# Flip sign convention
tensor_with_flipped_convention = inertia_tensor.with_given_integral_convention(
    mp.IntegralConvention.negative,
)
# Load from string
sample_json_values = """
{
    "xx": 1.0,
    "yy": 1.0,
    "zz": 1.0,
    "xy": 0,
    "zx": 0,
    "yz": 0,
    "integral_convention": "negative"
}
"""
loaded_values = mp.InertiaTensor.model_validate_json(sample_json_values)

# Print values
# memory
print(
    "inertia_tensor.model_dump_json(indent=4):\n",
    inertia_tensor.model_dump_json(indent=4),
)
print(
    "inertia_tensor.array:\n",
    inertia_tensor.array,
)
# flipped convention
print(
    "tensor_with_flipped_convention.model_dump_json(indent=4):\n",
    tensor_with_flipped_convention.model_dump_json(indent=4),
)
print(
    "tensor_with_flipped_convention.array:\n",
    tensor_with_flipped_convention.array,
)
# loaded from string
print(
    "loaded_values.model_dump_json(indent=4):\n",
    loaded_values.model_dump_json(indent=4),
)
print(
    "loaded_values.array:\n",
    loaded_values.array,
)
