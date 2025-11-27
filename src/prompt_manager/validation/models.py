"""
Pydantic models for schema validation definitions.

Provides a type-safe representation of YAML schema definitions.
"""

from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FieldType(str, Enum):
    """Supported field data types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ENUM = "enum"
    ANY = "any"


class ValidationType(str, Enum):
    """Supported validation types."""

    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    RANGE = "range"
    REGEX = "regex"
    ENUM = "enum"
    CUSTOM = "custom"
    EMAIL = "email"
    URL = "url"
    UUID = "uuid"
    DATE = "date"
    DATETIME = "datetime"


class FieldValidator(BaseModel):
    """
    Validator configuration for a schema field.

    Defines validation rules that will be applied to field values.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: ValidationType
    value: Any = None
    error_message: str | None = None

    # Type-specific parameters
    min_value: int | float | None = None
    max_value: int | float | None = None
    pattern: str | None = None
    allowed_values: list[Any] | None = None
    custom_function: str | None = None

    @model_validator(mode="after")
    def validate_validator_params(self) -> "FieldValidator":
        """Validate that required parameters are present for validator type."""
        if self.type == ValidationType.REGEX and not self.pattern:
            msg = "Regex validator requires 'pattern' parameter"
            raise ValueError(msg)

        if self.type == ValidationType.ENUM and not self.allowed_values:
            msg = "Enum validator requires 'allowed_values' parameter"
            raise ValueError(msg)

        if self.type == ValidationType.RANGE:
            if self.min_value is None or self.max_value is None:
                msg = "Range validator requires 'min_value' and 'max_value' parameters"
                raise ValueError(msg)

        if self.type == ValidationType.CUSTOM and not self.custom_function:
            msg = "Custom validator requires 'custom_function' parameter"
            raise ValueError(msg)

        return self


class SchemaField(BaseModel):
    """
    Schema field definition.

    Represents a single field in a schema with its type, constraints, and validators.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    name: str = Field(..., min_length=1)
    type: FieldType
    required: bool = Field(default=True)
    default: Any = None
    description: str | None = None

    # Nested schema support
    nested_schema: str | None = None  # Reference to another schema by name
    item_type: FieldType | None = None  # For list types
    item_schema: str | None = None  # For list of objects

    # Validators
    validators: list[FieldValidator] = Field(default_factory=list)

    # Additional constraints
    nullable: bool = Field(default=False)
    read_only: bool = Field(default=False)
    write_only: bool = Field(default=False)

    @field_validator("name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        """Validate field name is a valid identifier."""
        if not v.replace("_", "").replace("-", "").isalnum():
            msg = "Field name must be alphanumeric (underscores and hyphens allowed)"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_list_configuration(self) -> "SchemaField":
        """Validate list type configuration."""
        if self.type == FieldType.LIST:
            if not self.item_type and not self.item_schema:
                msg = "List type requires either 'item_type' or 'item_schema'"
                raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_dict_configuration(self) -> "SchemaField":
        """Validate dict type configuration."""
        if self.type == FieldType.DICT and not self.nested_schema:
            # Allow plain dict without schema
            pass
        return self

    @model_validator(mode="after")
    def validate_default_value(self) -> "SchemaField":
        """Validate that default value is provided for non-required fields."""
        if not self.required and self.default is None and not self.nullable:
            msg = f"Non-required field '{self.name}' should have a default value or be nullable"
            raise ValueError(msg)
        return self


class Schema(BaseModel):
    """
    Complete schema definition.

    Represents a full data schema with multiple fields and metadata.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    name: str = Field(..., min_length=1)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    description: str | None = None

    # Schema fields - use Annotated to apply min_length constraint
    fields: Annotated[list[SchemaField], Field(min_length=1)]

    # Metadata
    strict: bool = Field(default=True)  # If True, reject extra fields
    allow_extra: bool = Field(default=False)  # If True, allow extra fields
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Inheritance
    extends: str | None = None  # Reference to parent schema

    @field_validator("name")
    @classmethod
    def validate_schema_name(cls, v: str) -> str:
        """Validate schema name."""
        if not v.replace("_", "").replace("-", "").isalnum():
            msg = "Schema name must be alphanumeric (underscores and hyphens allowed)"
            raise ValueError(msg)
        return v

    @field_validator("fields")
    @classmethod
    def validate_unique_field_names(cls, v: list[SchemaField]) -> list[SchemaField]:
        """Validate that field names are unique."""
        names = [field.name for field in v]
        if len(names) != len(set(names)):
            msg = "Field names must be unique within schema"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_strict_settings(self) -> "Schema":
        """Validate strict and allow_extra are not both True."""
        if self.strict and self.allow_extra:
            msg = "Cannot have both 'strict' and 'allow_extra' set to True"
            raise ValueError(msg)
        return self

    def get_field(self, name: str) -> SchemaField | None:
        """
        Get a field by name.

        Args:
            name: Field name to look up

        Returns:
            SchemaField if found, None otherwise
        """
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def get_required_fields(self) -> list[SchemaField]:
        """
        Get all required fields.

        Returns:
            List of required schema fields
        """
        return [field for field in self.fields if field.required]

    def get_optional_fields(self) -> list[SchemaField]:
        """
        Get all optional fields.

        Returns:
            List of optional schema fields
        """
        return [field for field in self.fields if not field.required]


class SchemaRegistry(BaseModel):
    """
    Registry of multiple schemas.

    Used when loading schemas from YAML files.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    schemas: list[Schema] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("schemas")
    @classmethod
    def validate_unique_schema_names(cls, v: list[Schema]) -> list[Schema]:
        """Validate that schema names are unique."""
        names = [schema.name for schema in v]
        if len(names) != len(set(names)):
            msg = "Schema names must be unique within registry"
            raise ValueError(msg)
        return v

    def get_schema(self, name: str) -> Schema | None:
        """
        Get a schema by name.

        Args:
            name: Schema name to look up

        Returns:
            Schema if found, None otherwise
        """
        for schema in self.schemas:
            if schema.name == name:
                return schema
        return None

    def add_schema(self, schema: Schema) -> None:
        """
        Add a schema to the registry.

        Args:
            schema: Schema to add

        Raises:
            ValueError: If schema name already exists
        """
        if self.get_schema(schema.name):
            msg = f"Schema '{schema.name}' already exists in registry"
            raise ValueError(msg)
        self.schemas.append(schema)

    def remove_schema(self, name: str) -> bool:
        """
        Remove a schema from the registry.

        Args:
            name: Schema name to remove

        Returns:
            True if schema was removed, False if not found
        """
        for i, schema in enumerate(self.schemas):
            if schema.name == name:
                self.schemas.pop(i)
                return True
        return False
