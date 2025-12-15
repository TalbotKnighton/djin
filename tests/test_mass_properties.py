from pathlib import Path
from typing import Annotated
from djin import (
    mass_properties as mp,
    frames as f,
    math_objects as mo,
    containers as c,
    transforms as t,
)
from pydantic import Field


def test_frame_transforms():
    """
    Docstring for test_mass_properties_transforms
    """
    Catalogue = Annotated[f.Frame | mp.MassProperties, Field(discriminator="type")]
    with c.Warehouse[Catalogue](id="Warehouse").set_context() as wh:
        a = f.Frame(
            pose=mo.Pose3D(
                position=mo.Point3D(
                    vector=mo.VectorR3(
                        data=(
                            0,
                            1,
                            0,
                        ),
                    ),
                ),
                orientation=mo.Orientation3D(
                    quaternion=mo.Quaternion(
                        data=(
                            0,
                            0,
                            0,
                            1,
                        ),
                    )
                ),
            )
        ).stow()
        b = f.Frame(
            pose=mo.Pose3D(
                position=mo.Point3D(
                    vector=mo.VectorR3(
                        data=(
                            0,
                            1,
                            0,
                        ),
                    ),
                ),
                orientation=mo.Orientation3D(
                    quaternion=mo.Quaternion(
                        data=(
                            0,
                            0,
                            0,
                            1,
                        ),
                    )
                ),
            ),
            parent_id=a.id,
        ).stow()
        mass_props = mp.MassProperties(
            mass=1,
            pose=mo.Pose3D(
                position=mo.Point3D(
                    vector=mo.VectorR3(
                        data=(
                            0,
                            1,
                            0,
                        ),
                    ),
                ),
                orientation=mo.Orientation3D(
                    quaternion=mo.Quaternion(
                        data=(
                            0,
                            0,
                            0,
                            1,
                        ),
                    )
                ),
            ),
            inertia_tensor=mp.InertiaTensor(
                xx=1,
                yy=1,
                zz=1,
                xy=0,
                zx=0,
                yz=0,
                integral_convention=mp.IntegralConvention.positive,
            ),
            frame=b.id,
        ).stow()

        wh_dump = wh.model_dump_json(
            indent=4,
        )
        b_a1 = t.to_parent_frame(transformable=b, starting_frame=a)
        b_a1_dump = b_a1.model_dump_json(indent=4)
        b_a2 = b.contents.to_parent_frame(warehouse=wh)
        b_a2_dump = b_a2.model_dump_json(indent=4)
        mp_a1 = t.to_parent_frame(
            mass_props,
            starting_frame=b,
            warehouse=wh,
        )
        mp_a2 = mass_props.contents.to_parent_frame(warehouse=wh)
        mp_a1_dump = mp_a1.model_dump_json(indent=4)
        mp_a2_dump = mp_a2.model_dump_json(indent=4)
        Path(
            __file__,
        ).with_suffix(
            ".out",
        ).write_text(
            "\n\n".join(
                [
                    wh_dump,
                    b_a1_dump,
                    b_a2_dump,
                    mass_props.model_dump_json(indent=4),
                    mp_a1_dump,
                    mp_a2_dump,
                ]
            )
        )


if __name__ == "__main__":
    test_frame_transforms()
