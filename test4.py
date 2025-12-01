import djin as dj

f1 = dj.frames.Frame(
    pose=dj.math_objects.Pose3D(
        components=(
            dj.math_objects.VectorR3(),
            dj.math_objects.Quaternion(),
        ),
    ),
)
print(f1.model_dump_json(indent=2))
print(f1.to_ground_frame().model_dump_json(indent=2))

f2 = dj.frames.Frame
