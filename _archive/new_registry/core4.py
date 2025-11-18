from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import ClassVar, Optional, Self, Any
import inspect
import numpy as np

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    computed_field,
    field_validator,
    model_validator,
    ValidationError,
)

IDType = str | int

OBJECT_REGISTRY = "object_registry"


def _get_registry_type_key(obj: type | str):
    if hasattr(obj, "get_registry_type_key"):
        return obj.get_registry_type_key()
    if not isinstance(obj, (str, bytes)):
        return obj.__name__
    return str(obj)


from importlib import import_module
from pathlib import Path
from typing import Self, Any, Optional
import inspect
import sys
import importlib.util

from pydantic import BaseModel, ValidationError, field_validator


class ImportSpec(BaseModel):
    """
    Specifies how to import a Python object by its module and object specification.

    The format follows 'module_path:object_spec' where object_spec can optionally
    include a method in the format 'Class.method'. An optional alias can be specified
    to indicate the name under which the object is imported.
    """

    module_spec: str
    object_spec: str
    alias: Optional[str] = None  # New field for the alias
    version: Optional[str] = None  # New field for the version

    @field_validator("module_spec", mode="before")
    @classmethod
    def validate_module_spec(cls, module_spec: str | Path) -> str:
        """Validates and converts module_spec to a string."""
        if isinstance(module_spec, Path):
            module_spec = str(module_spec.resolve())
        if not isinstance(module_spec, str):
            raise ValidationError(
                f"Module spec should be given as a string or a Path. Given {module_spec = }"
            )
        return module_spec

    @field_validator("object_spec", mode="after")
    @classmethod
    def validate_object_spec(cls, object_spec: str) -> str:
        """Validates object_spec format."""
        if len(object_spec.split(".")) > 2:
            raise ValidationError(
                f"Method spec should have no more than 1 `.` in it {object_spec = }"
            )
        return object_spec

    @classmethod
    def from_string(cls, spec: str, alias: Optional[str] = None) -> Self:
        """
        Creates an ImportSpec from a string in format 'module_path:object_spec'.

        Args:
            spec: The import specification string.
            alias: Optional alias name for the imported object.

        Returns:
            An ImportSpec instance.
        """
        module_spec, object_spec = tuple(spec.split(":"))
        return cls(
            module_spec=module_spec,
            object_spec=object_spec,
            alias=alias,
        )

    @classmethod
    def from_obj(cls, obj: Any, alias: Optional[str] = None) -> Self:
        """
        Creates an ImportSpec from a Python object using inspect.

        For objects defined in packages, this uses the standard module path.
        For objects defined outside of packages (e.g., in standalone scripts),
        this uses the absolute file path as the module name.

        Args:
            obj: The Python object to create an ImportSpec for.
            alias: Optional alias name for the object.

        Returns:
            An ImportSpec that can be used to import the object.
        """
        import inspect
        import os
        from pathlib import Path

        # Get the object's module
        if hasattr(obj, "__module__"):
            module_name = obj.__module__
        elif inspect.ismodule(obj):
            module_name = obj.__name__
        else:
            module_name = obj.__class__.__module__

        # Get the object specification
        if inspect.ismodule(obj):
            object_spec = ""  # No object spec for modules
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            object_spec = obj.__qualname__
            # If it's a method of a class, ensure we only keep Class.method format
            if "." in object_spec:
                parts = object_spec.split(".")
                if len(parts) > 2:
                    object_spec = f"{parts[-2]}.{parts[-1]}"
        elif inspect.isclass(obj):
            object_spec = obj.__name__
        else:
            # For instances
            object_spec = obj.__class__.__name__

        # Check if object is defined in "__main__" or another non-package module
        if module_name == "__main__" or (
            module_name != "builtins" and "." not in module_name
        ):
            # Try to get the file where the object is defined
            try:
                # For classes and functions
                if inspect.isclass(obj) or inspect.isfunction(obj):
                    file_path = inspect.getfile(obj)
                # For instances
                elif hasattr(obj, "__class__"):
                    file_path = inspect.getfile(obj.__class__)
                # For modules
                elif inspect.ismodule(obj) and hasattr(obj, "__file__"):
                    file_path = obj.__file__
                else:
                    # Fallback to current file if we can't determine the source
                    file_path = inspect.currentframe().f_back.f_code.co_filename

                # Convert to absolute path
                abs_path = str(Path(file_path).resolve())

                # Use the absolute path as the module spec
                module_name = abs_path
            except (TypeError, ValueError, AttributeError):
                # If we can't get the file, just use the module name as is
                pass

        # Get alias if not provided
        if alias is None and hasattr(obj, "__alias__"):
            alias = obj.__alias__

        return cls(
            module_spec=module_name,
            object_spec=object_spec,
            alias=alias,
        )

    def get_import(self) -> Any:
        """
        Imports and returns the object specified by this ImportSpec.

        Handles both standard module imports and imports from file paths.

        Returns:
            The imported Python object.
        """
        import importlib.util
        import sys
        from pathlib import Path

        module_spec = self.module_spec

        # Check if the module_spec is a file path
        if Path(module_spec).exists() and (
            module_spec.endswith(".py") or not module_spec.endswith(("/", "\\"))
        ):
            # It's a file path, load module from file
            path = Path(module_spec)
            if path.is_file():
                # Generate a unique module name based on the file path
                module_name = f"_dynamic_import_{hash(str(path))}"

                # Check if already imported
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                else:
                    # Create spec and load the module
                    spec = importlib.util.spec_from_file_location(
                        module_name, str(path)
                    )
                    if spec is None:
                        raise ImportError(f"Could not load spec for {path}")

                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                obj = module
            else:
                raise ImportError(f"File path does not exist or is not a file: {path}")
        else:
            # Standard module import
            obj = importlib.import_module(module_spec)

        # Return the module if no object is specified
        if not self.object_spec:
            return obj

        # Get the specified object
        if "." in self.object_spec:
            class_spec, method_spec = self.object_spec.split(".")
            obj = getattr(obj, class_spec)
            obj = getattr(obj, method_spec)
        else:
            obj = getattr(obj, self.object_spec)

        return obj

    def import_statement(self) -> str:
        """
        Generates a Python import statement for this ImportSpec.

        Returns:
            A string containing the Python import statement.
        """
        if not self.object_spec:
            if self.alias:
                return f"import {self.module_spec} as {self.alias}"
            return f"import {self.module_spec}"

        if self.alias:
            return f"from {self.module_spec} import {self.object_spec} as {self.alias}"
        return f"from {self.module_spec} import {self.object_spec}"

    def execute_import(
        self, globals_dict: dict = None, locals_dict: dict = None
    ) -> Any:
        """
        Executes the import in the specified namespace and returns the imported object.

        Args:
            globals_dict: The globals dictionary to use for the import.
            locals_dict: The locals dictionary to use for the import.

        Returns:
            The imported object.
        """
        if globals_dict is None:
            # Use the caller's globals by default
            import inspect

            frame = inspect.currentframe().f_back
            globals_dict = frame.f_globals
            locals_dict = frame.f_locals if locals_dict is None else locals_dict

        # Import the object
        obj = self.get_import()

        # Store it in the namespace with the appropriate name
        name = (
            self.alias
            if self.alias
            else (
                self.object_spec.split(".")[-1]
                if self.object_spec
                else self.module_spec.split(".")[-1]
            )
        )
        globals_dict[name] = obj

        return obj

    @classmethod
    def from_module_imports(cls, module) -> list[Self]:
        """
        Extracts ImportSpecs from a module's imports, including alias information.

        Args:
            module: The module to extract imports from.

        Returns:
            A list of ImportSpec objects representing the imports in the module.
        """
        import inspect
        import ast
        import os

        specs = []

        # Get the module's file
        if not hasattr(module, "__file__"):
            return specs

        file_path = module.__file__
        if not file_path or not os.path.exists(file_path):
            return specs

        # Parse the module's source code
        with open(file_path, "r") as f:
            source = f.read()

        try:
            tree = ast.parse(source)

            # Find import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Handle "import X" or "import X as Y"
                    for name in node.names:
                        specs.append(
                            cls(
                                module_spec=name.name, object_spec="", alias=name.asname
                            )
                        )
                elif isinstance(node, ast.ImportFrom):
                    # Handle "from X import Y" or "from X import Y as Z"
                    for name in node.names:
                        specs.append(
                            cls(
                                module_spec=node.module or "",
                                object_spec=name.name,
                                alias=name.asname,
                            )
                        )
        except SyntaxError:
            # If we can't parse the source, just return empty list
            pass

        return specs


class BaseComponent(BaseModel):
    """ """

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=False)

    # Attributes
    name: Optional[IDType] = None

    @computed_field
    def import_spec(self) -> ImportSpec:
        # return self.__class__.__name__
        return ImportSpec.from_obj(self)

    @classmethod
    def get_registry_type_key(cls):
        return cls.__name__

    def register(self, registry: Registry | ByTypeRegistry) -> Self:
        registry.add_object(self)


class Registry(BaseComponent):
    """ """

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=False)

    # Attributes
    instances: dict[IDType, SerializeAsAny[BaseComponent]] = Field({}, exclude=False)

    def get_next_unused_id(self) -> IDType:
        """Get the next unused ID"""
        return np.max([i for i in self.instances if isinstance(i, int)]) + 1

    def get_object(self, name: IDType):
        """Get an object from the registry by its ID."""
        if name in self.instances:
            return self.instances.get(name)
        raise ValueError(f"Object with ID {name} does not exist.")

    def add_object(self, obj: BaseComponent, allow_overwrite=True):
        """Add an object to the registry."""
        if not allow_overwrite and (obj.name in self.instances):
            raise ValueError(
                f"Object with name {obj.name = } already exists in {type(self).__name__} for {self.name}."
            )
        self.instances[obj.name] = obj
        return obj

    def remove_object(self, name: str):
        """Remove an object from the registry."""
        del self.instances[name]
        return self


class ByTypeRegistry(BaseComponent):
    """ """

    # Config
    model_config = ConfigDict(arbitrary_types_allowed=False)

    # Attributes
    types: dict[IDType, SerializeAsAny[Registry]] = Field({}, exclude=False)

    def get_object(self, t: type, name: IDType):
        """Get an object from the registry by its ID."""
        t = _get_registry_type_key(t)
        try:
            return self.types[t].get_object(name)
        except KeyError:
            raise ValueError(f"Object with ID {name} does not exist.")

    def add_object(
        self,
        obj: BaseComponent,
        allow_overwrite: bool = False,
    ):
        """Add an object to the registry."""
        t = _get_registry_type_key(obj)

        if t not in self.types:
            self.types[t] = Registry(name=t)

        self.types[t].add_object(
            obj,
            allow_overwrite=allow_overwrite,
        )

        return obj

    def remove_object(self, t: type, name: IDType):
        """Remove an object from the registry."""
        t = _get_registry_type_key(t)
        del self.types[t].instances[name]
        return self


class ByTypeRegistries(BaseModel):
    """ """

    registries: dict[str, ByTypeRegistry] = {
        OBJECT_REGISTRY: ByTypeRegistry(
            name=OBJECT_REGISTRY,
        ),
    }

    def get_next_unused_id(self) -> IDType:
        """Get the next unused ID"""
        return np.max([i for i in self.registries if isinstance(i, int)]) + 1

    def get_registry(self, name: IDType, add_if_not_exists: bool = True):
        """Get an object from the registry by its ID."""
        if not name in self.registries:
            if add_if_not_exists:
                return self.add_registry(ByTypeRegistry(name=name))
            else:
                raise ValueError(f"Registry with ID {name} does not exist.")
        else:
            return self.registries.get(name)

    def add_registry(self, registry: ByTypeRegistry, allow_overwrite=True):
        """Add an object to the registry."""
        if not allow_overwrite and (registry.name in self.registries):
            raise ValueError(f"Registry with ID {registry.name} already exists.")
        self.registries[registry.name] = registry
        return registry

    def remove_registry(self, name: str):
        """Remove an object from the registry."""
        del self.registries[name]
        return self

    def load_registry(
        self,
        path: Path,
        allow_overwrite: bool = False,
    ):
        btr = ByTypeRegistry.model_validate_json(
            path.read_text(),
        )
        self.add_registry(
            btr,
            allow_overwrite=allow_overwrite,
        )
        return btr


registries = ByTypeRegistries()


class ByTypeComponent(BaseComponent):
    """ """

    @model_validator(mode="after")
    def register(self):
        registries.get_registry(OBJECT_REGISTRY).add_object(self)
        # registries.get_registry("type_registry").add_object(
        #     ImportSpec.from_obj(self), allow_overwrite=True
        # )
        return self


class ByTypeReference(BaseModel):
    """ """

    type: str
    name: IDType

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        if not isinstance(v, str):
            return v.__name__
        return v

    def get_object(self):
        return registries.get_registry(
            name=OBJECT_REGISTRY,
        ).get_object(
            type=self.type,
            name=self.name,
        )

    def remove_object(self):
        return registries.get_registry(
            name=OBJECT_REGISTRY,
        ).remove_object(
            type=self.type,
            name=self.name,
        )


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

    @computed_field
    def import_spec(self) -> ImportSpec:
        # return self.__class__.__name__
        return ImportSpec.from_obj(self)

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
