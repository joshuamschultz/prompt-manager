"""
Schema loader for loading YAML schemas and converting to Pydantic validators.

Provides loading and caching of schema definitions.
"""

from pathlib import Path
from typing import Any, Type, cast

import structlog
import yaml
from pydantic import BaseModel, ConfigDict, create_model

from prompt_manager.exceptions import SchemaParseError, SchemaValidationError
from prompt_manager.validation.models import (
    FieldType,
    Schema,
    SchemaField,
    SchemaRegistry,
    ValidationType,
)
from prompt_manager.validation.validators import ValidatorFactory

logger = structlog.get_logger(__name__)


class SchemaLoader:
    """
    Loader for YAML schema definitions.

    Supports loading schemas from YAML files and converting them to
    Pydantic models for runtime validation.
    """

    def __init__(self) -> None:
        """Initialize schema loader."""
        self._logger = logger.bind(component="schema_loader")
        self._schema_cache: dict[str, Schema] = {}
        self._model_cache: dict[str, Type[BaseModel]] = {}

    def load_file(self, filepath: Path) -> SchemaRegistry:
        """
        Load schemas from a YAML file.

        Usage:
            registry = loader.load_file(Path("schemas.yaml"))

        Args:
            filepath: Path to YAML file

        Returns:
            Schema registry with loaded schemas

        Raises:
            SchemaParseError: If YAML parsing fails
            SchemaValidationError: If validation fails
        """
        self._logger.info("loading_schema_file", file=str(filepath))

        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Parse YAML
            data = yaml.safe_load(content)

            if not data:
                msg = "Empty YAML file"
                raise SchemaParseError(msg, file=str(filepath))

            # Validate with Pydantic
            registry = SchemaRegistry.model_validate(data)

            # Cache schemas
            for schema in registry.schemas:
                self._schema_cache[schema.name] = schema

            self._logger.info(
                "schema_file_loaded",
                file=str(filepath),
                schema_count=len(registry.schemas),
            )

            return registry

        except SchemaParseError:
            # Re-raise SchemaParseError as-is
            raise
        except yaml.YAMLError as e:
            msg = f"Invalid YAML syntax: {e}"
            raise SchemaParseError(msg, file=str(filepath)) from e
        except Exception as e:
            msg = f"Failed to validate schema: {e}"
            raise SchemaValidationError(msg, file=str(filepath)) from e

    def load_directory(self, dirpath: Path) -> list[SchemaRegistry]:
        """
        Load all YAML schema files from a directory.

        Usage:
            registries = loader.load_directory(Path("schemas/"))

        Args:
            dirpath: Directory path

        Returns:
            List of loaded schema registries

        Raises:
            SchemaParseError: If any file fails to parse
        """
        self._logger.info("loading_schema_directory", path=str(dirpath))

        registries = []
        yaml_files = list(dirpath.glob("*.yaml")) + list(dirpath.glob("*.yml"))

        for filepath in yaml_files:
            try:
                registry = self.load_file(filepath)
                registries.append(registry)
            except Exception as e:
                self._logger.error(
                    "failed_to_load_schema_file",
                    file=str(filepath),
                    error=str(e),
                )
                # Continue with other files
                continue

        self._logger.info(
            "schema_directory_loaded",
            path=str(dirpath),
            registry_count=len(registries),
        )

        return registries

    def get_schema(self, name: str) -> Schema | None:
        """
        Get a cached schema by name.

        Args:
            name: Schema name

        Returns:
            Schema if found, None otherwise
        """
        return self._schema_cache.get(name)

    def create_pydantic_model(
        self,
        schema: Schema,
        *,
        model_name: str | None = None,
    ) -> Type[BaseModel]:
        """
        Create a Pydantic model from a schema definition.

        Args:
            schema: Schema definition
            model_name: Optional custom model name

        Returns:
            Dynamically created Pydantic model class

        Raises:
            ValueError: If schema references are invalid
        """
        name = model_name or schema.name
        self._logger.debug("creating_pydantic_model", schema=name)

        # Check cache
        if name in self._model_cache:
            return self._model_cache[name]

        # Build field definitions
        field_definitions: dict[str, Any] = {}

        for field in schema.fields:
            field_type = self._get_python_type(field)
            field_info = self._create_field_info(field)

            # Handle required vs optional
            if field.required and not field.nullable:
                field_definitions[field.name] = (field_type, field_info)
            elif field.nullable:
                field_definitions[field.name] = (field_type | None, field_info)
            else:
                field_definitions[field.name] = (field_type | None, field_info)

        # Create model config
        config = ConfigDict(
            extra="forbid" if schema.strict else "allow",
            frozen=False,
            validate_assignment=True,
        )

        # Create the model
        model = create_model(
            name,
            __config__=config,
            **field_definitions,
        )

        # Cache the model
        self._model_cache[name] = model

        self._logger.debug("pydantic_model_created", schema=name, fields=len(field_definitions))

        return cast(Type[BaseModel], model)

    def _get_python_type(self, field: SchemaField) -> Any:
        """
        Convert schema field type to Python type.

        Args:
            field: Schema field

        Returns:
            Python type annotation (may be a generic type like list[str])
        """
        type_mapping = {
            FieldType.STRING: str,
            FieldType.INTEGER: int,
            FieldType.FLOAT: float,
            FieldType.BOOLEAN: bool,
            FieldType.LIST: list,
            FieldType.DICT: dict,
            FieldType.ANY: Any,
        }

        base_type = type_mapping.get(field.type)
        if not base_type:
            msg = f"Unknown field type: {field.type}"
            raise ValueError(msg)

        # Handle list with item type
        if field.type == FieldType.LIST and field.item_type:
            item_type = type_mapping.get(field.item_type, Any)
            return list[item_type]  # type: ignore[valid-type]

        # Handle nested schema
        if field.nested_schema:
            nested_schema = self.get_schema(field.nested_schema)
            if not nested_schema:
                msg = f"Nested schema not found: {field.nested_schema}"
                raise ValueError(msg)
            return self.create_pydantic_model(nested_schema)

        return base_type

    def _create_field_info(self, field: SchemaField) -> Any:
        """
        Create Pydantic Field info from schema field.

        Args:
            field: Schema field

        Returns:
            Pydantic Field instance
        """
        from pydantic import Field

        field_kwargs: dict[str, Any] = {}

        # Add description
        if field.description:
            field_kwargs["description"] = field.description

        # Add default value
        if field.default is not None:
            field_kwargs["default"] = field.default
        elif not field.required:
            field_kwargs["default"] = None

        # Add validators
        validators = []
        for validator_config in field.validators:
            try:
                validator = ValidatorFactory.create_validator(
                    {
                        "type": validator_config.type.value,
                        "min_value": validator_config.min_value,
                        "max_value": validator_config.max_value,
                        "pattern": validator_config.pattern,
                        "allowed_values": validator_config.allowed_values,
                        "error_message": validator_config.error_message,
                    }
                )
                validators.append(validator)
            except Exception as e:
                self._logger.warning(
                    "failed_to_create_validator",
                    field=field.name,
                    validator_type=validator_config.type,
                    error=str(e),
                )

        # Apply type-specific constraints
        if field.type == FieldType.STRING:
            for validator_config in field.validators:
                if validator_config.type == ValidationType.MIN_LENGTH:
                    field_kwargs["min_length"] = validator_config.min_value
                elif validator_config.type == ValidationType.MAX_LENGTH:
                    field_kwargs["max_length"] = validator_config.max_value
                elif validator_config.type == ValidationType.REGEX:
                    field_kwargs["pattern"] = validator_config.pattern

        elif field.type in (FieldType.INTEGER, FieldType.FLOAT):
            for validator_config in field.validators:
                if validator_config.type == ValidationType.MIN_VALUE:
                    field_kwargs["ge"] = validator_config.min_value
                elif validator_config.type == ValidationType.MAX_VALUE:
                    field_kwargs["le"] = validator_config.max_value

        elif field.type == FieldType.LIST:
            for validator_config in field.validators:
                if validator_config.type == ValidationType.MIN_LENGTH:
                    field_kwargs["min_length"] = validator_config.min_value
                elif validator_config.type == ValidationType.MAX_LENGTH:
                    field_kwargs["max_length"] = validator_config.max_value

        return Field(**field_kwargs)

    def validate_data(
        self,
        schema_name: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate data against a schema.

        Usage:
            validated = loader.validate_data("user_profile", data)

        Args:
            schema_name: Name of schema to validate against
            data: Data to validate

        Returns:
            Validated data (may be transformed by Pydantic)

        Raises:
            ValueError: If schema not found
            SchemaValidationError: If validation fails
        """
        schema = self.get_schema(schema_name)
        if not schema:
            msg = f"Schema '{schema_name}' not found"
            raise ValueError(msg)

        try:
            model = self.create_pydantic_model(schema)
            instance = model.model_validate(data)
            return instance.model_dump()
        except Exception as e:
            msg = f"Validation failed for schema '{schema_name}': {e}"
            raise SchemaValidationError(msg, schema=schema_name, data=data) from e

    def clear_cache(self) -> None:
        """Clear all cached schemas and models."""
        self._schema_cache.clear()
        self._model_cache.clear()
        self._logger.info("cache_cleared")

    @staticmethod
    def create_example_schema(output_path: Path) -> None:
        """
        Create an example schema YAML file.

        Args:
            output_path: Where to write the example file
        """
        example = {
            "version": "1.0.0",
            "metadata": {
                "description": "Example schema definitions",
                "author": "System",
            },
            "schemas": [
                {
                    "name": "user_profile",
                    "version": "1.0.0",
                    "description": "User profile schema",
                    "strict": True,
                    "fields": [
                        {
                            "name": "username",
                            "type": "string",
                            "required": True,
                            "description": "Unique username",
                            "validators": [
                                {
                                    "type": "min_length",
                                    "min_value": 3,
                                    "error_message": "Username must be at least 3 characters",
                                },
                                {
                                    "type": "max_length",
                                    "max_value": 20,
                                    "error_message": "Username must be at most 20 characters",
                                },
                                {
                                    "type": "regex",
                                    "pattern": "^[a-zA-Z0-9_]+$",
                                    "error_message": "Username can only contain letters, numbers, and underscores",
                                },
                            ],
                        },
                        {
                            "name": "email",
                            "type": "string",
                            "required": True,
                            "description": "User email address",
                            "validators": [
                                {"type": "email"},
                            ],
                        },
                        {
                            "name": "age",
                            "type": "integer",
                            "required": False,
                            "default": None,
                            "nullable": True,
                            "description": "User age",
                            "validators": [
                                {
                                    "type": "range",
                                    "min_value": 13,
                                    "max_value": 120,
                                    "error_message": "Age must be between 13 and 120",
                                },
                            ],
                        },
                        {
                            "name": "role",
                            "type": "enum",
                            "required": True,
                            "default": "user",
                            "description": "User role",
                            "validators": [
                                {
                                    "type": "enum",
                                    "allowed_values": ["user", "admin", "moderator"],
                                },
                            ],
                        },
                        {
                            "name": "tags",
                            "type": "list",
                            "item_type": "string",
                            "required": False,
                            "default": [],
                            "description": "User tags",
                            "validators": [
                                {
                                    "type": "max_length",
                                    "max_value": 10,
                                    "error_message": "Maximum 10 tags allowed",
                                },
                            ],
                        },
                        {
                            "name": "metadata",
                            "type": "dict",
                            "required": False,
                            "default": {},
                            "description": "Additional metadata",
                        },
                    ],
                },
                {
                    "name": "api_config",
                    "version": "1.0.0",
                    "description": "API configuration schema",
                    "strict": True,
                    "fields": [
                        {
                            "name": "endpoint",
                            "type": "string",
                            "required": True,
                            "description": "API endpoint URL",
                            "validators": [
                                {"type": "url"},
                            ],
                        },
                        {
                            "name": "timeout",
                            "type": "integer",
                            "required": False,
                            "default": 30,
                            "description": "Request timeout in seconds",
                            "validators": [
                                {
                                    "type": "range",
                                    "min_value": 1,
                                    "max_value": 300,
                                },
                            ],
                        },
                        {
                            "name": "retry_count",
                            "type": "integer",
                            "required": False,
                            "default": 3,
                            "description": "Number of retries",
                            "validators": [
                                {
                                    "type": "range",
                                    "min_value": 0,
                                    "max_value": 10,
                                },
                            ],
                        },
                    ],
                },
            ],
        }

        with output_path.open("w") as f:
            yaml.dump(example, f, default_flow_style=False, sort_keys=False)

        logger.info("example_schema_created", path=str(output_path))
