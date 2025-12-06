import djin as dj

wh = dj.containers.Warehouse[dj.frames.Frame](id="wh")

with wh.set_context():
    a = dj.frames.Frame(
        pose=dj.math_objects.Pose3D(
            position=dj.math_objects.Point3D(
                vector=dj.math_objects.VectorR3(
                    data=(
                        0.0,
                        1.0,
                        0.0,
                    )
                ),
            ),
            orientation=dj.math_objects.Orientation3D(
                quaternion=dj.math_objects.Quaternion(),
            ),
        ),
        parent_id=None,
    ).stow()
    b = dj.frames.Frame(
        pose=dj.math_objects.Pose3D(
            position=dj.math_objects.Point3D(
                vector=dj.math_objects.VectorR3(
                    data=(
                        0.0,
                        1.0,
                        0.0,
                    )
                ),
            ),
            orientation=dj.math_objects.Orientation3D(
                quaternion=dj.math_objects.Quaternion(),
            ),
        ),
        parent_id=a.id,
    ).stow()
    _ = b.contents.parent.unpack()
    wh_loaded = dj.containers.Warehouse[dj.frames.Frame].model_validate_json(
        wh.model_dump_json()
    )
    print(wh.model_dump_json(indent=2))
    print(wh_loaded.model_dump_json(indent=2))
    with wh_loaded.set_context():
        c = dj.frames.Frame(
            pose=dj.math_objects.Pose3D(
                position=dj.math_objects.Point3D(
                    vector=dj.math_objects.VectorR3(),
                ),
                orientation=dj.math_objects.Orientation3D(
                    quaternion=dj.math_objects.Quaternion(),
                ),
            ),
            parent_id=None,
        ).stow()

    print(wh.model_dump_json(indent=2))
    print(wh_loaded.model_dump_json(indent=2))
    print(a.id)
    print(wh_loaded.unpack(id=a.id))
    print("\n\n\n")
    print(b.contents)
    print(b.contents.to_parent_frame())

try:
    c = dj.frames.Frame(
        pose=dj.math_objects.Pose3D(
            position=dj.math_objects.Point3D(
                vector=dj.math_objects.VectorR3(),
            ),
            orientation=dj.math_objects.Orientation3D(
                quaternion=dj.math_objects.Quaternion(),
            ),
        ),
        parent_id=None,
    ).stow()
except RuntimeError:
    print("Good, the context exited")
