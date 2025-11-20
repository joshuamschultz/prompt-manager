# Schema Validation System

Comprehensive YAML schema validation system for the prompt manager, providing type-safe data validation using Pydantic.

## Overview

The schema validation system allows you to:

- Define data schemas in YAML files
- Load and validate schemas programmatically
- Create dynamic Pydantic models from schemas
- Validate data against defined schemas
- Support nested schemas and complex data structures
- Use built-in validators (length, range, regex, email, URL, etc.)

## Architecture

### Core Components

1. **Models** (`validation/models.py`)
   - `FieldType`: Enum of supported field types
   - `ValidationType`: Enum of supported validation types
   - `FieldValidator`: Configuration for field validators
   - `SchemaField`: Individual field definition
   - `Schema`: Complete schema definition
   - `SchemaRegistry`: Collection of schemas

2. **Validators** (`validation/validators.py`)
   - `BaseValidator`: Abstract base class for all validators
   - `LengthValidator`: String/list length validation
   - `RangeValidator`: Numeric range validation
   - `RegexValidator`: Pattern matching validation
   - `EnumValidator`: Choice/enum validation
   - `EmailValidator`: Email address validation
   - `URLValidator`: URL validation
   - `UUIDValidator`: UUID validation
   - `DateValidator`: Date validation
   - `DateTimeValidator`: DateTime validation
   - `CustomValidator`: Custom function validation
   - `ValidatorFactory`: Factory for creating validators

3. **Loader** (`validation/loader.py`)
   - `SchemaLoader`: Load YAML schemas and create Pydantic models
   - Async file and directory loading
   - Schema caching
   - Dynamic model generation

## Field Types

### Supported Types

| Type | Python Type | Description |
|------|-------------|-------------|
| `string` | `str` | Text strings |
| `integer` | `int` | Integer numbers |
| `float` | `float` | Floating-point numbers |
| `boolean` | `bool` | True/False values |
| `list` | `list` | Arrays of items |
| `dict` | `dict` | Key-value objects |
| `enum` | Various | Enumerated choices |
| `any` | `Any` | Any type |

### Type-Specific Features

**Lists:**
- Specify `item_type` for typed lists
- Specify `item_schema` for lists of objects
- Validate list length

**Dicts:**
- Specify `nested_schema` for structured objects
- Support plain dicts without schemas

**Enums:**
- Use with `enum` validator
- Restrict values to allowed list

## Validators

### Built-in Validators

#### Length Validation

Validates string or list length.

```yaml
validators:
  - type: min_length
    min_value: 3
    error_message: "Must be at least 3 characters"
  - type: max_length
    max_value: 100
    error_message: "Must be at most 100 characters"
```

#### Range Validation

Validates numeric ranges.

```yaml
validators:
  - type: min_value
    min_value: 0
  - type: max_value
    max_value: 100
  - type: range
    min_value: 0
    max_value: 100
    error_message: "Must be between 0 and 100"
```

#### Regex Validation

Validates against regular expression patterns.

```yaml
validators:
  - type: regex
    pattern: "^[a-zA-Z0-9_]+$"
    error_message: "Only alphanumeric and underscore allowed"
```

#### Enum Validation

Restricts values to allowed list.

```yaml
validators:
  - type: enum
    allowed_values: ["admin", "user", "guest"]
    error_message: "Invalid role"
```

#### Email Validation

Validates email addresses.

```yaml
validators:
  - type: email
    error_message: "Invalid email address"
```

#### URL Validation

Validates URLs.

```yaml
validators:
  - type: url
    error_message: "Invalid URL"
```

#### UUID Validation

Validates UUIDs.

```yaml
validators:
  - type: uuid
    error_message: "Invalid UUID"
```

#### Date/DateTime Validation

Validates dates and datetimes.

```yaml
validators:
  - type: date
    format: "%Y-%m-%d"  # Optional, defaults to ISO 8601
  - type: datetime
    format: "%Y-%m-%dT%H:%M:%S"  # Optional
```

### Custom Validators

Create custom validators in Python:

```python
from prompt_manager.validation.validators import CustomValidator

def validate_username(value: str) -> bool:
    # Custom validation logic
    return value.isalnum() and len(value) >= 3

validator = CustomValidator(
    validator_func=validate_username,
    error_message="Invalid username"
)
```

## YAML Schema Format

### Basic Schema

```yaml
version: "1.0.0"
metadata:
  description: "My schemas"
  author: "Your Name"

schemas:
  - name: "user"
    version: "1.0.0"
    description: "User profile schema"
    strict: true

    fields:
      - name: "username"
        type: "string"
        required: true
        description: "Unique username"
        validators:
          - type: "min_length"
            min_value: 3
          - type: "max_length"
            max_value: 20
          - type: "regex"
            pattern: "^[a-zA-Z0-9_]+$"

      - name: "email"
        type: "string"
        required: true
        validators:
          - type: "email"

      - name: "age"
        type: "integer"
        required: false
        nullable: true
        validators:
          - type: "range"
            min_value: 13
            max_value: 120
```

### Nested Schemas

```yaml
schemas:
  - name: "address"
    version: "1.0.0"
    fields:
      - name: "street"
        type: "string"
        required: true
      - name: "city"
        type: "string"
        required: true
      - name: "postal_code"
        type: "string"
        required: true

  - name: "user_with_address"
    version: "1.0.0"
    fields:
      - name: "name"
        type: "string"
        required: true
      - name: "address"
        type: "dict"
        nested_schema: "address"
        required: true
```

### Lists and Arrays

```yaml
fields:
  # Simple list
  - name: "tags"
    type: "list"
    item_type: "string"
    required: false
    default: []
    validators:
      - type: "max_length"
        max_value: 10

  # List of objects
  - name: "addresses"
    type: "list"
    item_schema: "address"
    required: false
    default: []
```

### Enums

```yaml
fields:
  - name: "role"
    type: "enum"
    required: true
    default: "user"
    validators:
      - type: "enum"
        allowed_values: ["admin", "user", "guest"]
```

### Field Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | Required | Field name |
| `type` | FieldType | Required | Field data type |
| `required` | boolean | `true` | Whether field is required |
| `default` | any | `null` | Default value if not provided |
| `description` | string | `null` | Field description |
| `nullable` | boolean | `false` | Whether field can be null |
| `read_only` | boolean | `false` | Field is read-only |
| `write_only` | boolean | `false` | Field is write-only |
| `validators` | list | `[]` | List of validators |
| `nested_schema` | string | `null` | Reference to nested schema |
| `item_type` | FieldType | `null` | Type for list items |
| `item_schema` | string | `null` | Schema for list items |

### Schema Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | Required | Schema name |
| `version` | string | `"1.0.0"` | Semantic version |
| `description` | string | `null` | Schema description |
| `fields` | list | Required | List of fields |
| `strict` | boolean | `true` | Reject extra fields |
| `allow_extra` | boolean | `false` | Allow extra fields |
| `extends` | string | `null` | Parent schema name |
| `metadata` | dict | `{}` | Additional metadata |

## Usage Examples

### Loading Schemas

```python
from pathlib import Path
from prompt_manager.validation import SchemaLoader

# Create loader
loader = SchemaLoader()

# Load from file
registry = await loader.load_file(Path("schemas.yaml"))

# Load from directory
registries = await loader.load_directory(Path("schemas/"))

# Get cached schema
schema = loader.get_schema("user")
```

### Creating Pydantic Models

```python
# Create model from schema
UserModel = loader.create_pydantic_model(schema)

# Use model for validation
user = UserModel(
    username="john_doe",
    email="john@example.com",
    age=25
)

# Access validated data
print(user.username)  # "john_doe"
print(user.model_dump())  # Dict representation
```

### Validating Data

```python
# Validate data against schema
data = {
    "username": "john_doe",
    "email": "john@example.com",
    "age": 25
}

try:
    validated = await loader.validate_data("user", data)
    print("Validation successful!")
    print(validated)
except SchemaValidationError as e:
    print(f"Validation failed: {e}")
    print(f"Errors: {e.context.get('errors')}")
```

### Programmatic Schema Creation

```python
from prompt_manager.validation import (
    Schema,
    SchemaField,
    FieldType,
    ValidationType,
    FieldValidator,
)

# Create schema
schema = Schema(
    name="product",
    version="1.0.0",
    fields=[
        SchemaField(
            name="name",
            type=FieldType.STRING,
            required=True,
            validators=[
                FieldValidator(
                    type=ValidationType.MIN_LENGTH,
                    min_value=3
                )
            ]
        ),
        SchemaField(
            name="price",
            type=FieldType.FLOAT,
            required=True,
            validators=[
                FieldValidator(
                    type=ValidationType.RANGE,
                    min_value=0.01,
                    max_value=999999.99
                )
            ]
        )
    ]
)
```

### Working with Schema Registry

```python
from prompt_manager.validation.models import SchemaRegistry

# Create registry
registry = SchemaRegistry(schemas=[schema1, schema2])

# Get schema
schema = registry.get_schema("user")

# Add schema
registry.add_schema(new_schema)

# Remove schema
registry.remove_schema("old_schema")
```

## Advanced Features

### Schema Inheritance

Define base schemas and extend them:

```yaml
schemas:
  - name: "base_entity"
    version: "1.0.0"
    fields:
      - name: "id"
        type: "string"
        required: true
      - name: "created_at"
        type: "string"
        required: true

  - name: "user"
    version: "1.0.0"
    extends: "base_entity"
    fields:
      - name: "username"
        type: "string"
        required: true
```

### Custom Error Messages

Provide custom error messages for better UX:

```yaml
validators:
  - type: "min_length"
    min_value: 8
    error_message: "Password must be at least 8 characters long"
  - type: "regex"
    pattern: "^(?=.*[A-Z])(?=.*[0-9])"
    error_message: "Password must contain at least one uppercase letter and one number"
```

### Dynamic Field Defaults

```python
from datetime import datetime

SchemaField(
    name="created_at",
    type=FieldType.STRING,
    required=False,
    default=datetime.utcnow().isoformat()
)
```

### Caching

The loader caches schemas and models for performance:

```python
# Clear cache when needed
loader.clear_cache()

# Check if schema is cached
schema = loader.get_schema("user")
if schema:
    print("Schema found in cache")
```

## Integration with Prompt Manager

### Validating Prompt Variables

Use schemas to validate prompt template variables:

```yaml
schemas:
  - name: "email_prompt_vars"
    version: "1.0.0"
    fields:
      - name: "recipient_name"
        type: "string"
        required: true
      - name: "subject"
        type: "string"
        required: true
        validators:
          - type: "max_length"
            max_value: 100
      - name: "body"
        type: "string"
        required: true
```

```python
# Validate variables before rendering
variables = {
    "recipient_name": "John",
    "subject": "Welcome!",
    "body": "Thank you for signing up"
}

validated = await loader.validate_data("email_prompt_vars", variables)
prompt = await manager.render(prompt_id, validated)
```

### Input/Output Validation

Define schemas for prompt inputs and outputs:

```python
# Input schema
input_schema = Schema(name="prompt_input", fields=[...])

# Output schema
output_schema = Schema(name="prompt_output", fields=[...])

# Validate input
validated_input = await loader.validate_data("prompt_input", user_input)

# Render prompt
result = await manager.render(prompt_id, validated_input)

# Validate output
validated_output = await loader.validate_data("prompt_output", result)
```

## Error Handling

### Exception Hierarchy

- `SchemaError`: Base for all schema errors
  - `SchemaParseError`: YAML parsing failed
  - `SchemaValidationError`: Schema validation failed

### Handling Validation Errors

```python
from prompt_manager.exceptions import (
    SchemaParseError,
    SchemaValidationError,
)

try:
    registry = await loader.load_file(path)
except SchemaParseError as e:
    print(f"YAML parsing error: {e}")
    print(f"File: {e.context.get('file')}")
except SchemaValidationError as e:
    print(f"Schema validation error: {e}")
    print(f"Errors: {e.context.get('errors')}")
```

## Best Practices

### Schema Design

1. **Use Semantic Versioning**: Version schemas using semver (1.0.0)
2. **Provide Descriptions**: Document fields and schemas
3. **Set Appropriate Defaults**: Use sensible defaults for optional fields
4. **Validate Early**: Validate at system boundaries
5. **Keep Schemas Focused**: One schema per entity/concept
6. **Use Nested Schemas**: Reuse common structures
7. **Custom Error Messages**: Help users understand validation failures

### Performance

1. **Cache Schemas**: Let the loader cache loaded schemas
2. **Reuse Models**: Create Pydantic models once, reuse them
3. **Validate in Batches**: Group validation operations
4. **Use Strict Mode**: Enable strict validation for better performance

### Security

1. **Validate All Input**: Never trust external data
2. **Use Type Constraints**: Leverage validators for security
3. **Limit Sizes**: Set max lengths for strings and lists
4. **Sanitize Regex**: Be careful with user-provided patterns
5. **No Arbitrary Code**: Avoid custom validators with user code

## Testing

### Unit Tests

```python
import pytest
from prompt_manager.validation import Schema, SchemaField, FieldType

def test_schema_validation():
    schema = Schema(
        name="test",
        fields=[
            SchemaField(
                name="field",
                type=FieldType.STRING,
                required=True
            )
        ]
    )

    assert schema.name == "test"
    assert len(schema.fields) == 1
```

### Integration Tests

```python
async def test_end_to_end_validation():
    # Create schema file
    schema_path = tmp_path / "schema.yaml"
    # ... write schema

    # Load schema
    loader = SchemaLoader()
    registry = await loader.load_file(schema_path)

    # Validate data
    result = await loader.validate_data("test", data)

    assert result["field"] == "value"
```

## API Reference

See the inline documentation in:
- `/src/prompt_manager/validation/models.py`
- `/src/prompt_manager/validation/validators.py`
- `/src/prompt_manager/validation/loader.py`

## Examples

Complete examples available in:
- `/examples/schema_validation_example.py`

## Changelog

### Version 1.0.0
- Initial release
- Support for all basic field types
- Built-in validators (length, range, regex, enum, email, URL, UUID, date)
- YAML schema loading
- Dynamic Pydantic model generation
- Async support throughout
- Comprehensive test coverage
