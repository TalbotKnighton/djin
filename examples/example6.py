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
