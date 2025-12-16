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
