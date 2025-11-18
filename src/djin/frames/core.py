from contextvars import ContextVar
from typing import ClassVar
from djin.registry.core import Registry, Registrant

current_frame_registry = ContextVar("frame_registry", default=None)


class Frame(Registrant):
    _registry_type: ClassVar[str] = "Frame"


class FrameRegistry(Registry[Frame]):
    pass
