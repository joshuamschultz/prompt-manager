"""
Tests for schema validation system.

Comprehensive test suite for YAML schema validation functionality.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from prompt_manager.exceptions import SchemaParseError, SchemaValidationError
from prompt_manager.validation import (
    FieldType,
    Schema,
    SchemaField,
    SchemaLoader,
    ValidationType,
)
from prompt_manager.validation.models import FieldValidator, SchemaRegistry
from prompt_manager.validation.validators import (
    EmailValidator,
    EnumValidator,
    LengthValidator,
    RangeValidator,
    RegexValidator,
    URLValidator,
    UUIDValidator,
)


class TestFieldValidator:
    """Tests for FieldValidator model."""

    def test_create_basic_validator(self) -> None:
        """Test creating a basic validator."""
        validator = FieldValidator(
            type=ValidationType.MIN_LENGTH,
            min_value=5,
        )
        assert validator.type == ValidationType.MIN_LENGTH
        assert validator.min_value == 5

    def test_regex_validator_requires_pattern(self) -> None:
        """Test that regex validator requires pattern."""
        with pytest.raises(ValueError, match="pattern"):
            FieldValidator(type=ValidationType.REGEX)

    def test_enum_validator_requires_values(self) -> None:
        """Test that enum validator requires allowed values."""
        with pytest.raises(ValueError, match="allowed_values"):
            FieldValidator(type=ValidationType.ENUM)

    def test_range_validator_requires_min_max(self) -> None:
        """Test that range validator requires min and max values."""
        with pytest.raises(ValueError, match="min_value"):
            FieldValidator(type=ValidationType.RANGE, min_value=1)


class TestSchemaField:
    """Tests for SchemaField model."""

    def test_create_basic_field(self) -> None:
        """Test creating a basic schema field."""
        field = SchemaField(
            name="username",
            type=FieldType.STRING,
            required=True,
        )
        assert field.name == "username"
        assert field.type == FieldType.STRING
        assert field.required is True

    def test_field_name_validation(self) -> None:
        """Test field name validation."""
        # Valid names
        SchemaField(name="valid_name", type=FieldType.STRING)
        SchemaField(name="valid-name", type=FieldType.STRING)
        SchemaField(name="validName123", type=FieldType.STRING)

        # Invalid names
        with pytest.raises(ValueError):
            SchemaField(name="invalid name", type=FieldType.STRING)
        with pytest.raises(ValueError):
            SchemaField(name="invalid@name", type=FieldType.STRING)

    def test_optional_field_requires_default_or_nullable(self) -> None:
        """Test that optional fields need default or nullable."""
        with pytest.raises(ValueError, match="default value"):
            SchemaField(name="field", type=FieldType.STRING, required=False)

        # These should work
        SchemaField(name="field", type=FieldType.STRING, required=False, default="test")
        SchemaField(name="field", type=FieldType.STRING, required=False, nullable=True)

    def test_list_field_requires_item_type(self) -> None:
        """Test that list fields require item type or schema."""
        with pytest.raises(ValueError, match="item_type"):
            SchemaField(name="items", type=FieldType.LIST, required=False, default=[])

        # These should work
        SchemaField(
            name="items",
            type=FieldType.LIST,
            item_type=FieldType.STRING,
            required=False,
            default=[],
        )
        SchemaField(
            name="items",
            type=FieldType.LIST,
            item_schema="user",
            required=False,
            default=[],
        )

    def test_field_with_validators(self) -> None:
        """Test creating field with validators."""
        field = SchemaField(
            name="age",
            type=FieldType.INTEGER,
            required=True,
            validators=[
                FieldValidator(
                    type=ValidationType.RANGE,
                    min_value=0,
                    max_value=150,
                ),
            ],
        )
        assert len(field.validators) == 1
        assert field.validators[0].type == ValidationType.RANGE


class TestSchema:
    """Tests for Schema model."""

    def test_create_basic_schema(self) -> None:
        """Test creating a basic schema."""
        schema = Schema(
            name="user",
            fields=[
                SchemaField(name="username", type=FieldType.STRING, required=True),
                SchemaField(name="email", type=FieldType.STRING, required=True),
            ],
        )
        assert schema.name == "user"
        assert len(schema.fields) == 2

    def test_schema_name_validation(self) -> None:
        """Test schema name validation."""
        # Valid names
        Schema(
            name="valid_schema",
            fields=[SchemaField(name="field", type=FieldType.STRING, required=True)],
        )

        # Invalid names
        with pytest.raises(ValueError):
            Schema(
                name="invalid schema",
                fields=[SchemaField(name="field", type=FieldType.STRING, required=True)],
            )

    def test_unique_field_names(self) -> None:
        """Test that field names must be unique."""
        with pytest.raises(ValueError, match="unique"):
            Schema(
                name="test",
                fields=[
                    SchemaField(name="field", type=FieldType.STRING, required=True),
                    SchemaField(name="field", type=FieldType.INTEGER, required=True),
                ],
            )

    def test_strict_and_allow_extra_conflict(self) -> None:
        """Test that strict and allow_extra cannot both be True."""
        with pytest.raises(ValueError, match="strict"):
            Schema(
                name="test",
                fields=[SchemaField(name="field", type=FieldType.STRING, required=True)],
                strict=True,
                allow_extra=True,
            )

    def test_get_field(self) -> None:
        """Test getting a field by name."""
        schema = Schema(
            name="user",
            fields=[
                SchemaField(name="username", type=FieldType.STRING, required=True),
                SchemaField(name="email", type=FieldType.STRING, required=True),
            ],
        )
        field = schema.get_field("username")
        assert field is not None
        assert field.name == "username"

        assert schema.get_field("nonexistent") is None

    def test_get_required_fields(self) -> None:
        """Test getting required fields."""
        schema = Schema(
            name="user",
            fields=[
                SchemaField(name="username", type=FieldType.STRING, required=True),
                SchemaField(
                    name="age", type=FieldType.INTEGER, required=False, nullable=True
                ),
            ],
        )
        required = schema.get_required_fields()
        assert len(required) == 1
        assert required[0].name == "username"


class TestSchemaRegistry:
    """Tests for SchemaRegistry model."""

    def test_create_registry(self) -> None:
        """Test creating a schema registry."""
        registry = SchemaRegistry(
            schemas=[
                Schema(
                    name="user",
                    fields=[SchemaField(name="name", type=FieldType.STRING, required=True)],
                ),
            ],
        )
        assert len(registry.schemas) == 1

    def test_unique_schema_names(self) -> None:
        """Test that schema names must be unique in registry."""
        with pytest.raises(ValueError, match="unique"):
            SchemaRegistry(
                schemas=[
                    Schema(
                        name="user",
                        fields=[
                            SchemaField(name="name", type=FieldType.STRING, required=True)
                        ],
                    ),
                    Schema(
                        name="user",
                        fields=[
                            SchemaField(name="email", type=FieldType.STRING, required=True)
                        ],
                    ),
                ],
            )

    def test_get_schema(self) -> None:
        """Test getting a schema by name."""
        registry = SchemaRegistry(
            schemas=[
                Schema(
                    name="user",
                    fields=[SchemaField(name="name", type=FieldType.STRING, required=True)],
                ),
            ],
        )
        schema = registry.get_schema("user")
        assert schema is not None
        assert schema.name == "user"

    def test_add_schema(self) -> None:
        """Test adding a schema to registry."""
        registry = SchemaRegistry()
        schema = Schema(
            name="user",
            fields=[SchemaField(name="name", type=FieldType.STRING, required=True)],
        )
        registry.add_schema(schema)
        assert len(registry.schemas) == 1

    def test_add_duplicate_schema(self) -> None:
        """Test that adding duplicate schema raises error."""
        registry = SchemaRegistry()
        schema = Schema(
            name="user",
            fields=[SchemaField(name="name", type=FieldType.STRING, required=True)],
        )
        registry.add_schema(schema)

        with pytest.raises(ValueError, match="already exists"):
            registry.add_schema(schema)

    def test_remove_schema(self) -> None:
        """Test removing a schema from registry."""
        registry = SchemaRegistry(
            schemas=[
                Schema(
                    name="user",
                    fields=[SchemaField(name="name", type=FieldType.STRING, required=True)],
                ),
            ],
        )
        result = registry.remove_schema("user")
        assert result is True
        assert len(registry.schemas) == 0

        result = registry.remove_schema("nonexistent")
        assert result is False


class TestValidators:
    """Tests for validator implementations."""

    def test_length_validator(self) -> None:
        """Test length validator."""
        validator = LengthValidator(min_length=3, max_length=10)

        # Valid
        assert validator.validate("hello")[0] is True
        assert validator.validate([1, 2, 3])[0] is True

        # Too short
        assert validator.validate("ab")[0] is False

        # Too long
        assert validator.validate("a" * 20)[0] is False

        # Invalid type
        assert validator.validate(123)[0] is False

    def test_range_validator(self) -> None:
        """Test range validator."""
        validator = RangeValidator(min_value=0, max_value=100)

        # Valid
        assert validator.validate(50)[0] is True
        assert validator.validate(0)[0] is True
        assert validator.validate(100)[0] is True

        # Out of range
        assert validator.validate(-1)[0] is False
        assert validator.validate(101)[0] is False

        # Invalid type
        assert validator.validate("50")[0] is False

    def test_regex_validator(self) -> None:
        """Test regex validator."""
        validator = RegexValidator(pattern=r"^[a-z]+$")

        # Valid
        assert validator.validate("hello")[0] is True

        # Invalid
        assert validator.validate("Hello")[0] is False
        assert validator.validate("hello123")[0] is False
        assert validator.validate(123)[0] is False

    def test_enum_validator(self) -> None:
        """Test enum validator."""
        validator = EnumValidator(allowed_values=["admin", "user", "guest"])

        # Valid
        assert validator.validate("admin")[0] is True
        assert validator.validate("user")[0] is True

        # Invalid
        assert validator.validate("superuser")[0] is False

    def test_email_validator(self) -> None:
        """Test email validator."""
        validator = EmailValidator()

        # Valid
        assert validator.validate("test@example.com")[0] is True

        # Invalid
        assert validator.validate("not-an-email")[0] is False
        assert validator.validate(123)[0] is False

    def test_url_validator(self) -> None:
        """Test URL validator."""
        validator = URLValidator()

        # Valid
        assert validator.validate("https://example.com")[0] is True
        assert validator.validate("http://example.com/path")[0] is True

        # Invalid
        assert validator.validate("not-a-url")[0] is False
        assert validator.validate(123)[0] is False

    def test_uuid_validator(self) -> None:
        """Test UUID validator."""
        validator = UUIDValidator()

        # Valid
        assert validator.validate("550e8400-e29b-41d4-a716-446655440000")[0] is True

        # Invalid
        assert validator.validate("not-a-uuid")[0] is False
        assert validator.validate(123)[0] is False


class TestSchemaLoader:
    """Tests for SchemaLoader."""

    @pytest.fixture
    def loader(self) -> SchemaLoader:
        """Create a schema loader instance."""
        return SchemaLoader()

    @pytest.fixture
    def sample_schema_yaml(self) -> dict:
        """Sample schema YAML data."""
        return {
            "version": "1.0.0",
            "schemas": [
                {
                    "name": "user",
                    "version": "1.0.0",
                    "description": "User schema",
                    "strict": True,
                    "fields": [
                        {
                            "name": "username",
                            "type": "string",
                            "required": True,
                            "validators": [
                                {"type": "min_length", "min_value": 3},
                                {"type": "max_length", "max_value": 20},
                            ],
                        },
                        {
                            "name": "email",
                            "type": "string",
                            "required": True,
                            "validators": [{"type": "email"}],
                        },
                        {
                            "name": "age",
                            "type": "integer",
                            "required": False,
                            "nullable": True,
                            "validators": [
                                {
                                    "type": "range",
                                    "min_value": 0,
                                    "max_value": 150,
                                },
                            ],
                        },
                    ],
                },
            ],
        }

    async def test_load_file(
        self, loader: SchemaLoader, sample_schema_yaml: dict, tmp_path: Path
    ) -> None:
        """Test loading schema from file."""
        # Create temp file
        schema_file = tmp_path / "schema.yaml"
        with schema_file.open("w") as f:
            yaml.dump(sample_schema_yaml, f)

        # Load file
        registry = await loader.load_file(schema_file)

        assert len(registry.schemas) == 1
        assert registry.schemas[0].name == "user"
        assert len(registry.schemas[0].fields) == 3

    async def test_load_invalid_yaml(self, loader: SchemaLoader, tmp_path: Path) -> None:
        """Test loading invalid YAML."""
        schema_file = tmp_path / "invalid.yaml"
        with schema_file.open("w") as f:
            f.write("invalid: yaml: content:")

        with pytest.raises(SchemaParseError):
            await loader.load_file(schema_file)

    async def test_load_empty_file(self, loader: SchemaLoader, tmp_path: Path) -> None:
        """Test loading empty file."""
        schema_file = tmp_path / "empty.yaml"
        schema_file.touch()

        with pytest.raises(SchemaParseError, match="Empty"):
            await loader.load_file(schema_file)

    async def test_load_directory(
        self, loader: SchemaLoader, sample_schema_yaml: dict, tmp_path: Path
    ) -> None:
        """Test loading schemas from directory."""
        # Create multiple schema files
        for i in range(3):
            schema_file = tmp_path / f"schema{i}.yaml"
            with schema_file.open("w") as f:
                yaml.dump(sample_schema_yaml, f)

        # Load directory
        registries = await loader.load_directory(tmp_path)

        assert len(registries) == 3

    def test_get_schema(self, loader: SchemaLoader) -> None:
        """Test getting cached schema."""
        schema = Schema(
            name="test",
            fields=[SchemaField(name="field", type=FieldType.STRING, required=True)],
        )
        loader._schema_cache["test"] = schema

        result = loader.get_schema("test")
        assert result is not None
        assert result.name == "test"

    def test_create_pydantic_model(self, loader: SchemaLoader) -> None:
        """Test creating Pydantic model from schema."""
        schema = Schema(
            name="user",
            fields=[
                SchemaField(name="username", type=FieldType.STRING, required=True),
                SchemaField(name="age", type=FieldType.INTEGER, required=False, nullable=True),
            ],
        )

        model = loader.create_pydantic_model(schema)

        # Validate with model
        instance = model(username="testuser")
        assert instance.username == "testuser"
        assert instance.age is None

        # Test validation
        with pytest.raises(Exception):
            model()  # Missing required field

    async def test_validate_data(self, loader: SchemaLoader) -> None:
        """Test validating data against schema."""
        schema = Schema(
            name="user",
            fields=[
                SchemaField(name="username", type=FieldType.STRING, required=True),
                SchemaField(name="age", type=FieldType.INTEGER, required=False, nullable=True),
            ],
        )
        loader._schema_cache["user"] = schema

        # Valid data
        result = await loader.validate_data("user", {"username": "testuser", "age": 25})
        assert result["username"] == "testuser"
        assert result["age"] == 25

        # Invalid data
        with pytest.raises(SchemaValidationError):
            await loader.validate_data("user", {})  # Missing required field

    def test_clear_cache(self, loader: SchemaLoader) -> None:
        """Test clearing cache."""
        schema = Schema(
            name="test",
            fields=[SchemaField(name="field", type=FieldType.STRING, required=True)],
        )
        loader._schema_cache["test"] = schema

        loader.clear_cache()

        assert len(loader._schema_cache) == 0
        assert len(loader._model_cache) == 0

    def test_create_example_schema(self, tmp_path: Path) -> None:
        """Test creating example schema file."""
        output_file = tmp_path / "example.yaml"
        SchemaLoader.create_example_schema(output_file)

        assert output_file.exists()

        # Load and validate
        with output_file.open() as f:
            data = yaml.safe_load(f)

        assert "schemas" in data
        assert len(data["schemas"]) > 0
