from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, Optional, Self, TypeVar
import pydantic as pyd
from djin.base import immutable
from djin.containers.core import ID, Container, Ref, Warehouse, get_warehouse

if TYPE_CHECKING:
    from djin.frames.core import Frame


T = TypeVar("T", bound=tuple)


@immutable
class Transformable3D(pyd.BaseModel, Generic[T]):
    @abstractmethod
    def get_components(self) -> T:
        raise NotImplementedError("You must implement this method")

    @abstractmethod
    def get_component_field_names(
        self,
    ) -> tuple[str, ...]:
        raise NotImplementedError()

    @abstractmethod
    def get_components_in_parent_frame(
        self,
        starting_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> T:
        raise NotImplementedError()

    @abstractmethod
    def get_components_in_target_frame(
        self,
        starting_frame: Container[Frame],
        target_frame: Container[Frame],
        warehouse: Optional[Warehouse] = None,
    ) -> T:
        raise NotImplementedError()

    def with_new_components(self, components: T) -> Self:
        if not isinstance(self, pyd.BaseModel):
            raise ValueError(
                f"{Transformable3D.__qualname__} must be a mixin for a child of `pydantic.BaseModel`"
            )
        return self.model_copy(
            deep=True,
            update={
                fname: c
                for fname, c in zip(
                    self.get_component_field_names(),
                    components,
                )
            },
        )


TF = TypeVar("TF", bound=Transformable3D)


def _get_transformable_object(
    transformable: TF | ID | Container[TF],
    warehouse: Optional[Warehouse] = None,
) -> TF:
    if isinstance(transformable, Transformable3D):
        return transformable
    elif isinstance(transformable, Container):
        return transformable.contents
    else:
        return get_warehouse(warehouse=warehouse).unpack(id=transformable)


def to_parent_frame(
    transformable: TF | ID | Container[TF],
    starting_frame: Optional[ID | Container[Frame]] = None,
    warehouse: Optional[Warehouse] = None,
) -> TF:
    from djin.frames.core import Frame

    tf = _get_transformable_object(transformable=transformable, warehouse=warehouse)
    if starting_frame is None:  # Ground is parent of all frames
        return tf.model_copy(deep=True)
    else:
        return tf.with_new_components(
            components=tf.get_components_in_parent_frame(
                starting_frame=(
                    Ref[Frame](id=starting_frame).get()
                    if not isinstance(starting_frame, Container)
                    else starting_frame
                ),
                warehouse=warehouse,
            )
        )


def to_ground_frame(
    transformable: TF | ID | Container[TF],
    starting_frame: Optional[ID | Container[Frame]],
    warehouse: Optional[Warehouse] = None,
) -> TF:
    from djin.frames.core import Frame

    tf = _get_transformable_object(
        transformable=transformable,
        warehouse=warehouse,
    )
    if starting_frame is None:
        return tf.model_copy(deep=True)
    else:
        parent = (
            starting_frame.contents.parent.get(warehouse=warehouse)
            if isinstance(starting_frame, Container)
            else Ref[Frame](id=starting_frame).get(warehouse=warehouse)
        )
        up_one_level = to_parent_frame(
            transformable=tf,
            starting_frame=starting_frame,
            warehouse=warehouse,
        )
        return to_ground_frame(
            transformable=up_one_level,
            starting_frame=parent,
            warehouse=warehouse,
        )


def to_target_frame(
    transformable: TF | ID | Container[TF],
    starting_frame: Optional[ID | Container[Frame]],
    target_frame: Optional[ID | Container[Frame]],
    warehouse: Optional[Warehouse] = None,
) -> TF:
    from djin.frames.core import Frame

    tf = _get_transformable_object(
        transformable=transformable,
        warehouse=warehouse,
    )
    if target_frame is None:
        return to_ground_frame(
            transformable=tf,
            starting_frame=starting_frame,
            warehouse=warehouse,
        )
    else:
        return tf.with_new_components(
            components=tf.get_components_in_target_frame(
                starting_frame=(
                    Ref[Frame](id=starting_frame).get()
                    if not isinstance(starting_frame, Container)
                    else starting_frame
                ),
                target_frame=(
                    Ref[Frame](id=target_frame).get()
                    if not isinstance(target_frame, Container)
                    else target_frame
                ),
                warehouse=warehouse,
            )
        )
