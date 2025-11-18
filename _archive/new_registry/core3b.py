from __future__ import annotations

from typing import ClassVar, Type, Dict, Any, Optional, TypeVar, Generic, cast
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

# Import your existing classes
from djin.new_registry.core3 import (
    ImportSpec,
    BaseComponent,
    Registry,
    ByTypeRegistry,
    registries,
    OBJECT_REGISTRY,
    IDType,
)

T = TypeVar("T", bound="SerializableModel")


class SerializableModel(BaseComponent):
    """
    An extension of BaseComponent that uses ImportSpec for automatic
    class resolution during deserialization.

    This model can serialize itself to JSON with its type information and
    be reconstructed correctly without knowing the specific type in advance.
    """

    # Class configuration
    model_config = ConfigDict(arbitrary_types_allowed=False, populate_by_name=True)

    # Class can define a version for migration support
    model_version: ClassVar[str] = "1.0.0"

    # No need to add import_spec as a computed field - it's already in BaseComponent

    @classmethod
    def model_validate(cls: Type[T], obj: Dict[str, Any], **kwargs) -> T:
        """
        Validates and creates a model instance, using class information from the
        import spec if the incoming data is meant for another model type.
        """
        if cls == SerializableModel and isinstance(obj, dict) and "import_spec" in obj:
            # This is a base class deserialization - get the actual class
            spec_data = obj["import_spec"]

            # We can directly use the ImportSpec object if it's already a model
            if isinstance(spec_data, ImportSpec):
                spec = spec_data
            else:
                # Or create one from the dictionary
                spec = ImportSpec(**spec_data)

            actual_cls = spec.get_import()

            if not issubclass(actual_cls, SerializableModel):
                raise TypeError(
                    f"Imported class {actual_cls.__name__} is not a SerializableModel"
                )

            # Use the actual class to validate
            return actual_cls.model_validate(obj, **kwargs)

        # Normal validation with the known class
        return super().model_validate(obj, **kwargs)

    def model_dump_json(self, **kwargs) -> str:
        """
        Serialize model to JSON string, ensuring import spec is included.
        """
        # Make sure the import_spec is included in the output
        kwargs.setdefault("exclude_none", True)
        return super().model_dump_json(**kwargs)

    @classmethod
    def from_json(cls: Type[T], json_data: str) -> T:
        """
        Deserialize a model from JSON string, resolving the correct class.
        """
        data = json.loads(json_data)
        return cls.model_validate(data)

    @classmethod
    def from_file(cls: Type[T], file_path: str | Path) -> T:
        """
        Load a model from a JSON file, resolving the correct class.
        """
        path = Path(file_path)
        with open(path, "r") as f:
            json_data = f.read()
        return cls.from_json(json_data)

    def save_to_file(self, file_path: str | Path) -> None:
        """
        Save model to a JSON file, including its import specification.
        """
        path = Path(file_path)
        with open(path, "w") as f:
            f.write(self.model_dump_json())

    @classmethod
    def from_registry(cls: Type[T], registry_type: str, name: IDType) -> T:
        """
        Load a model from a registry by its type and name.
        """
        obj = registries.get_registry(OBJECT_REGISTRY).get_object(registry_type, name)
        if not isinstance(obj, cls):
            raise TypeError(f"Object {name} in registry is not a {cls.__name__}")
        return obj

    def register_in_registry(self, registry_name: str = OBJECT_REGISTRY) -> Self:
        """
        Register this model in the specified registry.
        """
        registries.get_registry(registry_name).add_object(self)
        return self


class SerializableCollection(SerializableModel):
    """
    A collection of SerializableModel objects that can be serialized and deserialized
    as a group while preserving their specific types.
    """

    items: list[SerializableModel] = []

    @classmethod
    def from_models(cls, models: list[SerializableModel]) -> SerializableCollection:
        """Create a collection from a list of models"""
        return cls(items=models)

    def append(self, model: SerializableModel) -> None:
        """Add a model to the collection"""
        self.items.append(model)

    def get_by_name(self, name: IDType) -> Optional[SerializableModel]:
        """Get a model from the collection by name"""
        for item in self.items:
            if item.name == name:
                return item
        return None

    def get_by_type(self, model_type: Type) -> list[SerializableModel]:
        """Get all models of a specific type"""
        return [item for item in self.items if isinstance(item, model_type)]


# Example of a migration system to handle version changes
class ModelMigrator:
    """Handles migrations between different versions of models"""

    _migrations: Dict[tuple[str, str, str], callable] = {}

    @classmethod
    def register_migration(
        cls,
        model_name: str,
        from_version: str,
        to_version: str,
        migration_func: callable,
    ) -> None:
        """Register a migration function for a specific model version transition"""
        cls._migrations[(model_name, from_version, to_version)] = migration_func

    @classmethod
    def migrate(cls, data: dict, target_version: Optional[str] = None) -> dict:
        """Migrate model data to the target version or latest version"""
        if "import_spec" not in data:
            return data

        # Get model info
        spec = ImportSpec(**data["import_spec"])
        model_cls = spec.get_import()

        # If no version info or already at target version, return as is
        if not hasattr(model_cls, "model_version"):
            return data

        model_name = model_cls.__name__
        current_version = data.get("model_version", "1.0.0")
        target_version = target_version or model_cls.model_version

        # If already at target version, return as is
        if current_version == target_version:
            return data

        # Find direct migration path or create multi-step path
        if (model_name, current_version, target_version) in cls._migrations:
            # Direct migration
            return cls._migrations[(model_name, current_version, target_version)](data)
        else:
            # Try to find a path through intermediate versions
            # This is a simplified approach - a real implementation would need a proper path-finding algorithm
            for key in cls._migrations:
                m_name, from_ver, to_ver = key
                if m_name == model_name and from_ver == current_version:
                    # Found a first step
                    intermediate_data = cls._migrations[key](data)
                    # Recursively migrate from the intermediate version
                    return cls.migrate(intermediate_data, target_version)

            # No migration path found
            raise ValueError(
                f"No migration path found from {current_version} to {target_version} for {model_name}"
            )
