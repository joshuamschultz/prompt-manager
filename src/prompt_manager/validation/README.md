# Schema Validation System

YAML-based schema validation for the prompt manager with dynamic Pydantic model generation.

## Quick Start

### 1. Define Schema in YAML

```yaml
version: "1.0.0"
schemas:
  - name: "user"
    version: "1.0.0"
    strict: true
    fields:
      - name: "username"
        type: "string"
        required: true
        validators:
          - type: "min_length"
            min_value: 3
          - type: "regex"
            pattern: "^[a-zA-Z0-9_]+$"

      - name: "email"
        type: "string"
        required: true
        validators:
          - type: "email"
```

### 2. Load and Use Schema

```python
from pathlib import Path
from prompt_manager.validation import SchemaLoader

# Load schema
loader = SchemaLoader()
registry = await loader.load_file(Path("schema.yaml"))

# Validate data
data = {"username": "john_doe", "email": "john@example.com"}
validated = await loader.validate_data("user", data)

# Or create Pydantic model
UserModel = loader.create_pydantic_model(registry.schemas[0])
user = UserModel(**data)
```

## Features

- **Field Types**: string, integer, float, boolean, list, dict, enum, any
- **Validators**: length, range, regex, enum, email, URL, UUID, date/datetime
- **Nested Schemas**: Support for complex data structures
- **Async Loading**: Async file and directory loading
- **Caching**: Automatic schema and model caching
- **Type Safety**: Full type hints with Pydantic v2

## File Structure

```
validation/
├── __init__.py          # Public API exports
├── models.py            # Pydantic models for schemas
├── validators.py        # Validator implementations
├── loader.py            # Schema loader with async support
└── README.md            # This file
```

## Documentation

See comprehensive documentation: `/docs/schema_validation.md`

## Examples

Run examples:
```bash
python examples/schema_validation_example.py
```

See example schemas: `/examples/schemas/example_schemas.yaml`

## Testing

Run tests:
```bash
pytest tests/test_validation.py -v
```

## API Overview

### Models

```python
from prompt_manager.validation import (
    Schema,           # Complete schema definition
    SchemaField,      # Individual field
    FieldValidator,   # Validator configuration
    FieldType,        # Enum of types
    ValidationType,   # Enum of validators
)
```

### Validators

```python
from prompt_manager.validation import (
    LengthValidator,
    RangeValidator,
    RegexValidator,
    EnumValidator,
    CustomValidator,
)
```

### Loader

```python
from prompt_manager.validation import SchemaLoader

loader = SchemaLoader()

# Load schemas
registry = await loader.load_file(path)
registries = await loader.load_directory(path)

# Get cached schema
schema = loader.get_schema(name)

# Create Pydantic model
Model = loader.create_pydantic_model(schema)

# Validate data
result = await loader.validate_data(schema_name, data)

# Clear cache
loader.clear_cache()
```

## Common Patterns

### Required vs Optional Fields

```yaml
# Required field
- name: "username"
  type: "string"
  required: true

# Optional with default
- name: "age"
  type: "integer"
  required: false
  default: null

# Optional nullable
- name: "bio"
  type: "string"
  required: false
  nullable: true
```

### Lists

```yaml
# Simple list
- name: "tags"
  type: "list"
  item_type: "string"
  required: false
  default: []

# List of objects
- name: "addresses"
  type: "list"
  item_schema: "address"
  required: false
  default: []
```

### Nested Objects

```yaml
- name: "address"
  type: "dict"
  nested_schema: "address"
  required: true
```

### Multiple Validators

```yaml
validators:
  - type: "min_length"
    min_value: 8
  - type: "regex"
    pattern: "^(?=.*[A-Z])(?=.*[0-9])"
    error_message: "Must contain uppercase and number"
```

## Error Handling

```python
from prompt_manager.exceptions import (
    SchemaParseError,
    SchemaValidationError,
)

try:
    registry = await loader.load_file(path)
    result = await loader.validate_data("user", data)
except SchemaParseError as e:
    # YAML parsing failed
    print(f"Parse error: {e}")
except SchemaValidationError as e:
    # Validation failed
    print(f"Validation error: {e}")
    print(f"Details: {e.context}")
```

## Best Practices

1. **Version your schemas** using semantic versioning
2. **Provide descriptions** for all fields and schemas
3. **Use custom error messages** for better UX
4. **Cache schemas** - let the loader handle it
5. **Validate early** at system boundaries
6. **Keep schemas focused** - one per entity
7. **Use nested schemas** to avoid duplication

## Performance Tips

- Schemas are cached after first load
- Pydantic models are cached per schema
- Use `strict=true` for better validation performance
- Clear cache only when schemas change

## Integration

### With Prompt Manager

```python
# Validate prompt variables
variables_schema = loader.get_schema("prompt_variables")
validated = await loader.validate_data("prompt_variables", user_vars)

# Render with validated data
result = await prompt_manager.render(prompt_id, validated)
```

### With API Endpoints

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()
loader = SchemaLoader()

@app.post("/users")
async def create_user(data: dict):
    try:
        validated = await loader.validate_data("user", data)
        # Create user with validated data
        return {"user": validated}
    except SchemaValidationError as e:
        raise HTTPException(400, detail=str(e))
```

## Contributing

When adding new validators:
1. Inherit from `BaseValidator`
2. Implement `validate()` method
3. Add to `ValidatorFactory`
4. Add tests in `test_validation.py`
5. Update documentation

## Version

Current version: 1.0.0

Last updated: 2024-11-19
