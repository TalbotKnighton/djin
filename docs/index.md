# Welcome to `djin`

Eventually, this will be a dynamics engine.

## Purpose

Simulate 6DOF rigid body dynamics

## Requirements

- Store data in a serializable/deserializable format
- Syntax that is easy to read
- Work with Python type-hinting

## Description

Immutable contents are stowed into mutable Containers in a Warehouse.  The mutable Containers are recalled from a dictionary by ID and their contents are unpacked for use as needed.

```mermaid
graph LR
    subgraph WH ["Warehouse"]

        subgraph C1 ["Container (Mutable)"]
            subgraph contents1 ["contents"]
                A2["A"]
            end
            subgraph i1 ["id"]
                id_i1["2"]
            end
        end
        subgraph C2 ["Container (Mutable)"]
            subgraph contents2 ["contents"]
                A1["A"]
            end
            subgraph i2 ["id"]
                id_i2["1"]
            end
            
        end
        Etc["..."]
    end
```

Using discriminated unions, a warehouse can be used to serialize/deserialize a `Catalogue` of multiple types of objects.  For example, suppose you have two types `A` and `B` with a discriminating literal field `model_type: Literal["A"] = "A"` and similarly for `model_type: Literal["B"] = "B"`.  You can declare this using Python type hinting as follows:

```python
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from djin import Warehouse

class A(BaseModel):
    model_type: Literal["A"] = "A"
    ...

class B(BaseModel):
    model_type: Literal["B"] = "B"
    ...

MyCatalogue = Annotated[
    A|B,
    Field(discriminator="model_type"),
]
# Build in memory
to_serialize = Warehouse[MyCatalogue](...)
# Or load from a file
deserialized = Warehouse[MyCatalogue].model_validate_json(...)
```
The warehouse would then look like:

```mermaid
graph LR
    subgraph WH ["Warehouse"]

        subgraph C1 ["Container (Mutable)"]
            subgraph contents1 ["contents"]
                A2["B"]
            end
            subgraph i1 ["id"]
                id_i1["2"]
            end
        end
        subgraph C2 ["Container (Mutable)"]
            subgraph contents2 ["contents"]
                A1["A"]
            end
            subgraph i2 ["id"]
                id_i2["1"]
            end
            
        end
        Etc["..."]
    end
```

Objects needing to cross-reference one another should Reference the container ID of the other object and unpack the object when needed.  This way the whole warehouse can serialize/deserialize in any order without recursion.  See the red blocks below:

```mermaid
graph LR
    subgraph WH ["Warehouse"]

        subgraph C1 ["Container (Mutable)"]
            subgraph contents1 ["contents"]
            subgraph F1 ["Frame (Immutable)"]
                pose_F1["pose"]
                parent_F1["parent=1"]
            end
            end
            subgraph i1 ["id"]
                id_i1["2"]
            end
            
            
        end
        subgraph C2 ["Container (Mutable)"]
            subgraph contents2 ["contents"]
                subgraph F2 ["Frame (Immutable)"]
                    pose_F2["pose"]
                    parent_F2["parent=None"]
                end
            end
            subgraph i2 ["id"]
                id_i2["1"]
            end
            
        end
        Etc["..."]
    end
    
    classDef red fill:none,stroke:#ff0000,color:#FFFFFF,stroke-width:3px;
    class i2 red;
    class parent_F1 red;
```

## Structure

### Composition

Pydantic makes it easy to nest models through composition.  This creates a nested json schema.  See online discussions of benefits of composition over inheritance ("has a" versus "is a").  The following diagram shows how composition is used to build the objects we need for defining and transforming mass properties.
```mermaid
---
config:
    theme: dark
    look: classinc
    title: Transformable
    layout: tidy-tree
---
classDiagram
    class Transformable~Components~{
        +get_component_field_names()
        +get_components()
        +get_components_in_parent_frame(...)
        +get_components_in_target_frame(...)
    }
    class Frame~Pose3D~{
        parent_id: Optional[ID] = None
        pose: Pose3D
        to_parent_frame(...)
        to_ground_frame(...)
        to_target_frame(...)
    }
    class MassProperties~Pose3D,InertiaTensor,Optional[ID]~{
        mass: float
        pose: Pose3D
        inertia_tensor: InertiaTensor
        frame: Optional[ID]
        to_parent_frame(...)
        to_ground_frame(...)
        to_target_frame(...)
    }
    class Pose3D~Point3D,Orientation3D~{
        position: Point3D
        orientation: Orientation3D
    }
    class Point3D~VectorR3~{
        vector: VectorR3
    }
    class Orientation3D~Quaternion~{
        vector: Quaternion
    }
    class Vector3D{
        vector: VectorR3
    }
    class VectorR3{
        data: tuple[float, float, float]
    }
    class Quaternion{
        data: tuple[float, float, float, float]
    }
    %% class Tensor3x3{
    %%     data: tuple[
    %%         tuple[float, float, float],
    %%         tuple[float, float, float],
    %%         tuple[float, float, float],
    %%     ]
    %% }
    class Tensor3x3Symmetric{
        xx: float
        yy: float
        zz: float
        xy: float
        zx: float
        yz: float
    }
    %% class Rotation{
    %%     data: tuple[float, float, float, float]
    %% }
    class InertiaTensor{
        integral_convention: IntegralConvention
    }
    Transformable <|-- Frame
    Transformable <|-- MassProperties
    Transformable <|-- Pose3D
    Transformable <|-- Point3D
    Transformable <|-- Orientation3D
    Transformable <|-- Vector3D
    Frame *-- Pose3D
    Pose3D *-- Point3D
    Pose3D *-- Orientation3D
    MassProperties *-- Pose3D
    Tensor3x3Symmetric <|-- InertiaTensor
    Point3D *-- VectorR3
    Vector3D *-- VectorR3
    Orientation3D *-- Quaternion
    MassProperties *-- InertiaTensor
```
```mermaid
flowchart LR

    subgraph TO ["Transformable Objects"]
        Frame[Frame]
        MassProperties[MassProperties]
    end

    subgraph TMO ["Transformable Math Objects"]
        Vector3D[Vector3D]
        Point3D[Point3D]
        Orientation3D[Orientation3D]
        Pose3D[Pose3D]

        Pose3D --> Point3D
        Pose3D --> Orientation3D
    end

    subgraph AMO ["Abstract Math Objects"]
        VectorR3[VectorR3]
        Tensor3x3[Tensor3x3]
        Tensor3x3Symmetric[Tensor3x3Symmetric]
        InertiaTensor[InertiaTensor]
        Quaternion[Quaternion]
        Rotation[Rotation]

        InertiaTensor --> Tensor3x3Symmetric
    end

    Frame --> Pose3D
    MassProperties --> Pose3D
    MassProperties --> InertiaTensor
    Vector3D --> VectorR3
    Point3D --> VectorR3
    Orientation3D --> Quaternion
```

### Transformation

The transformations are performed recursively (as necessary) by transforming the components of `Transformable` objects. The transformation function calls look like this:

```mermaid
graph LR


    to_parent_frame_1[to_parent_frame]
    to_ground_frame_1[to_ground_frame]
    to_target_frame[to_target_frame]

    to_ground_frame_2[to_ground_frame]
    in_ground_frame_1{"is in ground frame?"}
    in_ground_frame_2{"is in ground frame?"}
    to_parent_frame_2[to_parent_frame]
    get_components_in_parent_frame["get_components_in_parent_frame"]
    get_components_in_target_frame["get_components_in_target_frame"]
    transformed_1["transformed"]
    transformed_2["transformed"]
    deepcopy_1["deepcopy"]
    deepcopy_2["deepcopy"]
    target_is_ground{"target is ground frame?"}

    to_parent_frame_1 --> in_ground_frame_1
    in_ground_frame_1 -- "yes" --> deepcopy_1
    in_ground_frame_1 -- "no" --> get_components_in_parent_frame
    get_components_in_parent_frame --> transformed_1

    to_ground_frame_1 --> in_ground_frame_2
    in_ground_frame_2 -- "yes" --> deepcopy_2
    in_ground_frame_2 -- "no" --> to_parent_frame_2
    to_parent_frame_2 --> to_ground_frame_1

    to_target_frame --> target_is_ground
    target_is_ground -- "yes" --> to_ground_frame_2
    target_is_ground --> get_components_in_target_frame
    get_components_in_target_frame -->  transformed_2

    classDef red fill:none,stroke:#ff0000,color:#FFFFFF,stroke-width:3px;
    class get_components_in_parent_frame red;
    class get_components_in_target_frame red;

```

The user must provide the two component transformation functions: `get_components_in_parent_frame` and `get_components_in_target_frame`.  

!!! tip "Avoid Infinite Recursion"
    
    - For objects in the `Frame` class composition tree, the  `get_components_in_target_frame` transformation function can use the frame's recursive `to_ground_frame` method but not the frames `to_target_frame` method.
    - For objects outside of the `Frame` class composition tree, you can directly use the frame's `to_target_frame` method.  See the `MassProperties` transformation for example.
