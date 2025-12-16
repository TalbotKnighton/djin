# Examples

## Abstract Math Objects

### Vector3D

```python
import djin.math_objects as mo
import numpy as np

a = mo.VectorR3(data=(1, 0, 0))
b = mo.VectorR3.from_array(np.array([0, 1, 0]))
c = np.dot(a, b)

print(f"{a = }")
print(f"{b = }")
print(f"{c = }")
print(f"{a.model_dump_json() = }")
```

Expected output:

```text
a = VectorR3(data=(1.0, 0.0, 0.0))
b = VectorR3(data=(0.0, 1.0, 0.0))
c = np.float64(0.0)
a.model_dump_json() = '{"data":[1.0,0.0,0.0]}
```
### Symmetric Tensor 3x3

```python
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

```

Expected output:

```text
inertia_tensor.model_dump_json(indent=4):
 {
    "xx": 1.0,
    "yy": 1.0,
    "zz": 1.0,
    "xy": 0.1,
    "zx": 0.1,
    "yz": 0.1,
    "integral_convention": "positive"
}
inertia_tensor.array:
 [[ 1.  -0.1 -0.1]
 [-0.1  1.  -0.1]
 [-0.1 -0.1  1. ]]
tensor_with_flipped_convention.model_dump_json(indent=4):
 {
    "xx": 1.0,
    "yy": 1.0,
    "zz": 1.0,
    "xy": -0.1,
    "zx": -0.1,
    "yz": -0.1,
    "integral_convention": "negative"
}
tensor_with_flipped_convention.array:
 [[ 1.  -0.1 -0.1]
 [-0.1  1.  -0.1]
 [-0.1 -0.1  1. ]]
loaded_values.model_dump_json(indent=4):
 {
    "xx": 1.0,
    "yy": 1.0,
    "zz": 1.0,
    "xy": 0.0,
    "zx": 0.0,
    "yz": 0.0,
    "integral_convention": "negative"
}
loaded_values.array:
 [[1. 0. 0.]
 [0. 1. 0.]
 [0. 0. 1.]]
```

### Quaternions

```python
from itertools import product
from djin import math_objects as mo

u = mo.Quaternion(data=(0, 0, 0, 1))
i = mo.Quaternion(data=(1, 0, 0, 0))
j = mo.Quaternion(data=(0, 1, 0, 0))
k = mo.Quaternion(data=(0, 0, 1, 0))

sequence = [i, j, k, u]


def identify(q: mo.Quaternion) -> str:
    if q == i:
        return "i"
    if q == -i:
        return "-i"
    if q == j:
        return "j"
    if q == -j:
        return "-j"
    if q == k:
        return "k"
    if q == -k:
        return "-k"
    if q == u:
        return "1"
    if q == -u:
        return "-1"
    raise ValueError


for q1, q2 in product(sequence, sequence):
    print(f"{identify(q1)}*{identify(q2)}={identify(q1 * q2)}")

print(0 * i + 1 * j + 2 * k + 3 * u)
print(u + u)
```

Output:
```text
i*i=-1
i*j=k
i*k=-j
i*1=i
j*i=-k
j*j=-1
j*k=i
j*1=j
k*i=j
k*j=-i
k*k=-1
k*1=k
1*i=i
1*j=j
1*k=k
1*1=1
data=(0.0, 1.0, 2.0, 3.0)
data=(0.0, 0.0, 0.0, 2.0)
```

### Rotations

```python
import numpy as np
from djin import math_objects as mo

xhat = mo.VectorR3(data=(1, 0, 0))
yhat = mo.VectorR3(data=(0, 1, 0))
zhat = mo.VectorR3(data=(0, 0, 1))

rx = mo.Rotation.from_euler(
    seq="xyz",
    angles=(90, 0, 0),
    degrees=True,
)
ry = mo.Rotation.from_euler(
    seq="xyz",
    angles=(0, 90, 0),
    degrees=True,
)
rz = mo.Rotation.from_euler(
    seq="xyz",
    angles=(0, 0, 90),
    degrees=True,
)

q_rx = mo.Quaternion.from_rotation(rx)
q_ry = mo.Quaternion.from_rotation(ry)
q_rz = mo.Quaternion.from_rotation(rz)

# Show rotation matrices
print("rx(+90 deg):\n", rx.as_matrix().astype(int))
print("ry(+90 deg):\n", ry.as_matrix().astype(int))
print("rz(+90 deg):\n", rz.as_matrix().astype(int))

# Test them against the VectorR3 objects
print("rx(+90 deg)@xhat:", np.array(rx.as_matrix() @ xhat).astype(int))
print("ry(+90 deg)@xhat:", np.array(ry.as_matrix() @ xhat).astype(int))
print("rz(+90 deg)@xhat:", np.array(rz.as_matrix() @ xhat).astype(int))
print("rx(+90 deg)@yhat:", np.array(rx.as_matrix() @ yhat).astype(int))
print("ry(+90 deg)@yhat:", np.array(ry.as_matrix() @ yhat).astype(int))
print("rz(+90 deg)@yhat:", np.array(rz.as_matrix() @ yhat).astype(int))
print("rx(+90 deg)@zhat:", np.array(rx.as_matrix() @ zhat).astype(int))
print("ry(+90 deg)@zhat:", np.array(ry.as_matrix() @ zhat).astype(int))
print("rz(+90 deg)@zhat:", np.array(rz.as_matrix() @ zhat).astype(int))

# Show the corresponding quaternions
print(f"{q_rx = }")
print(f"{q_ry = }")
print(f"{q_rz = }")

# Test the quaternion multiplication
print(
    "q_rx@xhat@q_rx.conj():",
    np.array((q_rx * xhat * q_rx.conj()).vector).astype(int),
)
print(
    "q_ry@xhat@q_ry.conj():",
    np.array((q_ry * xhat * q_ry.conj()).vector).astype(int),
)
print(
    "q_rz@xhat@q_rz.conj():",
    np.array((q_rz * xhat * q_rz.conj()).vector).astype(int),
)
print(
    "q_rx@yhat@q_rx.conj():",
    np.array((q_rx * yhat * q_rx.conj()).vector).astype(int),
)
print(
    "q_ry@yhat@q_ry.conj():",
    np.array((q_ry * yhat * q_ry.conj()).vector).astype(int),
)
print(
    "q_rz@yhat@q_rz.conj():",
    np.array((q_rz * yhat * q_rz.conj()).vector).astype(int),
)
print(
    "q_rx@zhat@q_rx.conj():",
    np.array((q_rx * zhat * q_rx.conj()).vector).astype(int),
)
print(
    "q_ry@zhat@q_ry.conj():",
    np.array((q_ry * zhat * q_ry.conj()).vector).astype(int),
)
print(
    "q_rz@zhat@q_rz.conj():",
    np.array((q_rz * zhat * q_rz.conj()).vector).astype(int),
)
```

Expected output:

```text
rx(+90 deg):
 [[ 1  0  0]
 [ 0  0 -1]
 [ 0  1  0]]
ry(+90 deg):
 [[ 0  0  1]
 [ 0  1  0]
 [-1  0  0]]
rz(+90 deg):
 [[ 0 -1  0]
 [ 1  0  0]
 [ 0  0  1]]
rx(+90 deg)@xhat: [1 0 0]
ry(+90 deg)@xhat: [ 0  0 -1]
rz(+90 deg)@xhat: [0 1 0]
rx(+90 deg)@yhat: [0 0 1]
ry(+90 deg)@yhat: [0 1 0]
rz(+90 deg)@yhat: [-1  0  0]
rx(+90 deg)@zhat: [ 0 -1  0]
ry(+90 deg)@zhat: [1 0 0]
rz(+90 deg)@zhat: [0 0 1]
q_rx = Quaternion(data=(0.7071067811865475, 0.0, 0.0, 0.7071067811865476))
q_ry = Quaternion(data=(0.0, 0.7071067811865475, 0.0, 0.7071067811865476))
q_rz = Quaternion(data=(0.0, 0.0, 0.7071067811865475, 0.7071067811865476))
q_rx@xhat@q_rx.conj(): [1 0 0]
q_ry@xhat@q_ry.conj(): [ 0  0 -1]
q_rz@xhat@q_rz.conj(): [0 1 0]
q_rx@yhat@q_rx.conj(): [0 0 1]
q_ry@yhat@q_ry.conj(): [0 1 0]
q_rz@yhat@q_rz.conj(): [-1  0  0]
q_rx@zhat@q_rx.conj(): [ 0 -1  0]
q_ry@zhat@q_ry.conj(): [1 0 0]
q_rz@zhat@q_rz.conj(): [0 0 1]
```

## Warehouse and Containers

```python
from __future__ import annotations

from djin import containers as co
from typing import Annotated, Literal
from pydantic import BaseModel, Field


class A(BaseModel, co.Stowable):
    type: Literal["A"] = "A"
    data: float
    b_id: co.ID


class B(BaseModel, co.Stowable):
    type: Literal["B"] = "B"
    data: float
    a_id: co.ID


CatalogueAB = Annotated[
    A | B,
    Field(discriminator="type"),
]

WarehouseAB = co.Warehouse[CatalogueAB]

with WarehouseAB(id="wh").set_context() as wh:
    b_id = "some_reserved"  # TODO: better ID reservation process
    a = A(
        data=0,
        b_id=b_id,
    ).stow()
    b = B(
        data=1,
        a_id=a.id,
    ).stow(id=b_id)

    dump1 = wh.model_dump_json(indent=4)
    reloaded = WarehouseAB.model_validate_json(dump1)
    dump2 = reloaded.model_dump_json(indent=4)

    print(dump1)
    print(dump2)
    print(f"{dump1 == dump2 = }")
```

Expected output:

```text
{
    "type": "container",
    "id": "wh",
    "contents": {
        "0": {
            "type": "container",
            "id": 0,
            "contents": {
                "type": "A",
                "data": 0.0,
                "b_id": "some_reserved"
            }
        },
        "some_reserved": {
            "type": "container",
            "id": "some_reserved",
            "contents": {
                "type": "B",
                "data": 1.0,
                "a_id": 0
            }
        }
    }
}
{
    "type": "container",
    "id": "wh",
    "contents": {
        "0": {
            "type": "container",
            "id": 0,
            "contents": {
                "type": "A",
                "data": 0.0,
                "b_id": "some_reserved"
            }
        },
        "some_reserved": {
            "type": "container",
            "id": "some_reserved",
            "contents": {
                "type": "B",
                "data": 1.0,
                "a_id": 0
            }
        }
    }
}
dump1 == dump2 = True
```

## Transformable Objects

### Frames

`Frame`s can be used to define coordinate systems and transform math objects `Vector3D`, `Point3D`, `Orientation3D`.  The `Frame` itself also can be transformed to a new reference system.  The following example demonstrates the recursive `to_ground_frame` method.  Also available are `to_parent_frame` which goes one level up towards the ground frame or `to_target_frame` which transforms directly to any other frame (via recursive transform to ground).


```python
from djin import frames as fr
from djin import math_objects as mo
from djin import containers as co

# Define some simple displacements
no_displacement = mo.Point3D()
d1x = mo.Point3D.single_axis_displacement(axis=mo.Axis.x, distance=1)
d1y = mo.Point3D.single_axis_displacement(axis=mo.Axis.y, distance=1)
d1z = mo.Point3D.single_axis_displacement(axis=mo.Axis.z, distance=1)
# Define some simple rotations
no_rotation = mo.Orientation3D()
o90x = mo.Orientation3D.single_axis_rotation(axis=mo.Axis.x, angle=90, degrees=True)
o90y = mo.Orientation3D.single_axis_rotation(axis=mo.Axis.y, angle=90, degrees=True)
o90z = mo.Orientation3D.single_axis_rotation(axis=mo.Axis.z, angle=90, degrees=True)

# Set a warehouse of frames as a context
FrameWarehouse = co.Warehouse[fr.Frame]
with FrameWarehouse(id="Warehouse").set_context() as initial_warehouse:
    # Populate the warehouse
    frame_a = fr.Frame(
        pose=mo.Pose3D(
            position=d1x,  # Offset by 1 in x direction
            orientation=no_rotation,
        ),
    ).stow()
    frame_b = fr.Frame(
        pose=mo.Pose3D(
            position=d1x,  # Offset by 1 in x direction
            orientation=no_rotation,
        ),
        parent_id=frame_a.id,  # Reference to frame_a
    ).stow(id="b")

    # Dump to JSON
    dump1 = initial_warehouse.model_dump_json(indent=4)
    # Load back in from JSON
    loaded_warehouse = FrameWarehouse.model_validate_json(dump1)
    # Dump the loaded warehouse to check against original dump
    dump2 = loaded_warehouse.model_dump_json(indent=4)
    # Demonstrate that you can
    # unpack and transform a given frame from the loaded warehouse
    loaded_frame_b = loaded_warehouse.unpack(id="b")
    loaded_frame_b_position = loaded_frame_b.pose.position
    loaded_frame_b_position_in_ground_frame = (
        loaded_frame_b.to_ground_frame().pose.position
    )
    # Print results
    print("dump1:\n", dump1)
    print("dump2:\n", dump2)
    print(f"{dump1 == dump2 = }")

    print(
        "loaded_frame_b_position",
        loaded_frame_b_position.model_dump_json(indent=4),
    )
    print(
        "loaded_frame_b_position_in_ground_frame",
        loaded_frame_b_position_in_ground_frame.model_dump_json(indent=4),
    )
```

Expected output:

```text
dump1:
 {
    "type": "container",
    "id": "Warehouse",
    "contents": {
        "0": {
            "type": "container",
            "id": 0,
            "contents": {
                "type": "Frame",
                "parent_id": null,
                "pose": {
                    "type": "Pose3D",
                    "position": {
                        "type": "Point3D",
                        "vector": {
                            "data": [
                                1.0,
                                0.0,
                                0.0
                            ]
                        }
                    },
                    "orientation": {
                        "type": "Rotation3D",
                        "quaternion": {
                            "data": [
                                0.0,
                                0.0,
                                0.0,
                                1.0
                            ]
                        }
                    }
                }
            }
        },
        "b": {
            "type": "container",
            "id": "b",
            "contents": {
                "type": "Frame",
                "parent_id": 0,
                "pose": {
                    "type": "Pose3D",
                    "position": {
                        "type": "Point3D",
                        "vector": {
                            "data": [
                                1.0,
                                0.0,
                                0.0
                            ]
                        }
                    },
                    "orientation": {
                        "type": "Rotation3D",
                        "quaternion": {
                            "data": [
                                0.0,
                                0.0,
                                0.0,
                                1.0
                            ]
                        }
                    }
                }
            }
        }
    }
}
dump2:
 {
    "type": "container",
    "id": "Warehouse",
    "contents": {
        "0": {
            "type": "container",
            "id": 0,
            "contents": {
                "type": "Frame",
                "parent_id": null,
                "pose": {
                    "type": "Pose3D",
                    "position": {
                        "type": "Point3D",
                        "vector": {
                            "data": [
                                1.0,
                                0.0,
                                0.0
                            ]
                        }
                    },
                    "orientation": {
                        "type": "Rotation3D",
                        "quaternion": {
                            "data": [
                                0.0,
                                0.0,
                                0.0,
                                1.0
                            ]
                        }
                    }
                }
            }
        },
        "b": {
            "type": "container",
            "id": "b",
            "contents": {
                "type": "Frame",
                "parent_id": 0,
                "pose": {
                    "type": "Pose3D",
                    "position": {
                        "type": "Point3D",
                        "vector": {
                            "data": [
                                1.0,
                                0.0,
                                0.0
                            ]
                        }
                    },
                    "orientation": {
                        "type": "Rotation3D",
                        "quaternion": {
                            "data": [
                                0.0,
                                0.0,
                                0.0,
                                1.0
                            ]
                        }
                    }
                }
            }
        }
    }
}
dump1 == dump2 = True
loaded_frame_b_position {
    "type": "Point3D",
    "vector": {
        "data": [
            1.0,
            0.0,
            0.0
        ]
    }
}
loaded_frame_b_position_in_ground_frame {
    "type": "Point3D",
    "vector": {
        "data": [
            2.0,
            0.0,
            0.0
        ]
    }
}
```

### Vector3D

The `Vector3D` maintains its direction and magnitude (relative to the ground frame) under frame transformation.  Thus, it is used to represent forces, torques, etc.

!!! note "Example to be provided"

### Point3D

The `Point3D` component identifies a point in space.  Under frame transformation, the magnitude and direction change such that the vector gives the same point in space starting from the new origin.  So, use this to identify datums or points that are fixed spatially under frame transformation.

!!! note "Example to be provided"

### Orientation3D

The `Orientation3D` object defines a rotation relative to some given frame.  Under frame transformation, this object transforms such that the physical rotation is fixed.  So, if you have the orientation of a 3D object, frame transformation is like changing your frame of reference while keeping the physical orientation of the object fixed.

!!! note "Example to be provided"

### Mass Properties

The Mass properties object defines a mass and an inertia tensor and can be transformed to different reference frames.  The frame transformation must account for the parallel axis theorem and for the rotations.  Matrices can be rotated using `$RMR^T$` where `R` is a rotation matrix.  The way to think about this is that when left multiplying a given vector `v`, `R^T v` is a vector in the original frame of `M` and the final left multiplicaiton of `R` rotates back into the frame of vector `v` (todo: provide a link to some derivation).

```python
from typing import Annotated
from djin import frames as fr
from djin import mass_properties as mp
from djin import math_objects as mo
from djin import containers as co
import pydantic as pyd

from djin.mass_properties.core import MPCatalogue

# Define some simple displacements
no_displacement = mo.Point3D()
d1x = mo.Point3D.single_axis_displacement(axis=mo.Axis.x, distance=1)
d1y = mo.Point3D.single_axis_displacement(axis=mo.Axis.y, distance=1)
d1z = mo.Point3D.single_axis_displacement(axis=mo.Axis.z, distance=1)
# Define some simple rotations
no_rotation = mo.Orientation3D()
o90x = mo.Orientation3D.single_axis_rotation(axis=mo.Axis.x, angle=90, degrees=True)
o90y = mo.Orientation3D.single_axis_rotation(axis=mo.Axis.y, angle=90, degrees=True)
o90z = mo.Orientation3D.single_axis_rotation(axis=mo.Axis.z, angle=90, degrees=True)

print(o90z)
breakpoint()
# Set a warehouse of frames as a context

with mp.MPWarehouse().set_context() as initial_warehouse:
    # Populate the warehouse
    frame_a = fr.Frame(
        pose=mo.Pose3D(
            position=d1x,  # Offset by 1 in x direction
            orientation=no_rotation,
        ),
    ).stow(id="a")
    frame_b = fr.Frame(
        pose=mo.Pose3D(
            position=d1x,  # Offset by 1 in x direction
            orientation=no_rotation,
        ),
        parent_id=frame_a.id,  # Reference to frame_a
    ).stow(id="b")
    frame_c = fr.Frame(
        pose=mo.Pose3D(
            position=no_displacement,
            orientation=o90z,  # rotate about z axis
        ),
        parent_id=None,
    ).stow(id="c")

    point_mass = mp.MassProperties(
        mass=1,
        pose=mo.Pose3D(position=no_displacement, orientation=no_rotation),
        frame=frame_b.id,
        inertia_tensor=mp.InertiaTensor(
            xx=1,
            yy=2,
            zz=3,
            xy=0,
            zx=0,
            yz=0,
            integral_convention=mp.IntegralConvention.positive,
        ),
    ).stow()

    dump1 = initial_warehouse.model_dump_json(indent=4)
    loaded_warehouse = mp.MPWarehouse.model_validate_json(dump1)
    dump2 = loaded_warehouse.model_dump_json(indent=4)
    dump1_eq_dump2 = dump1 == dump2
    # Here is how to get the object with type hinting from the
    # loaded warehouse
    loaded_point_mass = co.ref(
        type=mp.MassProperties,
        id=point_mass.id,
    ).unpack(warehouse=loaded_warehouse)

    mass_props_in_frame_b = loaded_point_mass
    mass_props_in_frame_a = loaded_point_mass.to_parent_frame(
        warehouse=loaded_warehouse
    )
    mass_props_in_ground_frame = loaded_point_mass.to_ground_frame(
        warehouse=loaded_warehouse
    )
    mass_props_in_frame_c = loaded_point_mass.to_target_frame(
        target_frame=frame_c.id,
        warehouse=loaded_warehouse,
    )

    print(
        "mass_props_in_frame_b = ",
        mass_props_in_frame_b.model_dump_json(indent=4),
    )
    print(
        "mass_props_in_frame_a = ",
        mass_props_in_frame_a.model_dump_json(indent=4),
    )
    print(
        "mass_props_in_ground_frame = ",
        mass_props_in_ground_frame.model_dump_json(indent=4),
    )
    print(
        "mass_props_in_frame_c = ",
        mass_props_in_frame_c.model_dump_json(indent=4),
    )
```

!!! bug "Fix Rotation Transformations"

    There is clearly a bug in the rotation transformations, but this should be easy to fix.  I probably need to be more careful about active versus passive rotations and write out the equations...

Expected output:

```text
mass_props_in_frame_b =  {
    "type": "MassProperties",
    "mass": 1.0,
    "pose": {
        "type": "Pose3D",
        "position": {
            "type": "Point3D",
            "vector": {
                "data": [
                    0.0,
                    0.0,
                    0.0
                ]
            }
        },
        "orientation": {
            "type": "Rotation3D",
            "quaternion": {
                "data": [
                    0.0,
                    0.0,
                    0.0,
                    1.0
                ]
            }
        }
    },
    "inertia_tensor": {
        "xx": 1.0,
        "yy": 2.0,
        "zz": 3.0,
        "xy": 0.0,
        "zx": 0.0,
        "yz": 0.0,
        "integral_convention": "positive"
    },
    "frame": "b"
}
mass_props_in_frame_a =  {
    "type": "MassProperties",
    "mass": 1.0,
    "pose": {
        "type": "Pose3D",
        "position": {
            "type": "Point3D",
            "vector": {
                "data": [
                    1.0,
                    0.0,
                    0.0
                ]
            }
        },
        "orientation": {
            "type": "Rotation3D",
            "quaternion": {
                "data": [
                    0.0,
                    0.0,
                    0.0,
                    1.0
                ]
            }
        }
    },
    "inertia_tensor": {
        "xx": 1.0,
        "yy": 2.0,
        "zz": 3.0,
        "xy": 0.0,
        "zx": 0.0,
        "yz": 0.0,
        "integral_convention": "positive"
    },
    "frame": "a"
}
mass_props_in_ground_frame =  {
    "type": "MassProperties",
    "mass": 1.0,
    "pose": {
        "type": "Pose3D",
        "position": {
            "type": "Point3D",
            "vector": {
                "data": [
                    2.0,
                    0.0,
                    0.0
                ]
            }
        },
        "orientation": {
            "type": "Rotation3D",
            "quaternion": {
                "data": [
                    0.0,
                    0.0,
                    0.0,
                    1.0
                ]
            }
        }
    },
    "inertia_tensor": {
        "xx": 1.0,
        "yy": 2.0,
        "zz": 3.0,
        "xy": 0.0,
        "zx": 0.0,
        "yz": 0.0,
        "integral_convention": "positive"
    },
    "frame": null
}
mass_props_in_frame_c =  {
    "type": "MassProperties",
    "mass": 1.0,
    "pose": {
        "type": "Pose3D",
        "position": {
            "type": "Point3D",
            "vector": {
                "data": [
                    2.0,
                    -1.0,
                    0.0
                ]
            }
        },
        "orientation": {
            "type": "Rotation3D",
            "quaternion": {
                "data": [
                    0.0,
                    0.0,
                    -1.0,
                    2.220446049250313e-16
                ]
            }
        }
    },
    "inertia_tensor": {
        "xx": 1.0,
        "yy": 2.0,
        "zz": 3.0,
        "xy": -4.440892098500626e-16,
        "zx": 0.0,
        "yz": 0.0,
        "integral_convention": "positive"
    },
    "frame": "a"
}
```