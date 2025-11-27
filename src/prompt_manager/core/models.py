"""
Core domain models for the prompt management system.

Uses Pydantic v2 for validation, serialization, and type safety.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator


class PromptFormat(str, Enum):
    """Supported prompt formats."""

    TEXT = "text"
    CHAT = "chat"
    COMPLETION = "completion"
    INSTRUCTION = "instruction"


class PromptStatus(str, Enum):
    """Lifecycle status of a prompt."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Role(str, Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class Message(BaseModel):
    """A single chat message."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Role
    content: str
    name: str | None = None
    function_call: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v.strip():
            msg = "Message content cannot be empty"
            raise ValueError(msg)
        return v


class PromptMetadata(BaseModel):
    """Metadata associated with a prompt."""

    model_config = ConfigDict(extra="allow", frozen=False)

    author: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    use_cases: list[str] = Field(default_factory=list)
    model_recommendations: list[str] = Field(default_factory=list)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, gt=0)
    custom: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and normalize tags."""
        return [tag.strip().lower() for tag in v if tag.strip()]


class PromptTemplate(BaseModel):
    """Template configuration for a prompt."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    content: str
    variables: list[str] = Field(default_factory=list)
    partials: dict[str, str] = Field(default_factory=dict)
    helpers: dict[str, str] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v.strip():
            msg = "Template content cannot be empty"
            raise ValueError(msg)
        return v

    @field_validator("variables")
    @classmethod
    def validate_variables(cls, v: list[str]) -> list[str]:
        """Validate variable names."""
        if not all(var.isidentifier() for var in v):
            msg = "All variable names must be valid Python identifiers"
            raise ValueError(msg)
        return v


class ChatPromptTemplate(BaseModel):
    """Template configuration for chat prompts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    messages: list[Message]
    variables: list[str] = Field(default_factory=list)

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v: list[Message]) -> list[Message]:
        """Validate at least one message exists."""
        if not v:
            msg = "Chat prompt must have at least one message"
            raise ValueError(msg)
        return v


class Prompt(BaseModel):
    """
    Core prompt model with versioning and metadata.

    This is the primary domain model for the system.
    """

    model_config = ConfigDict(frozen=False, extra="forbid", validate_assignment=True, arbitrary_types_allowed=True)

    # Identity
    id: str = Field(..., min_length=1, max_length=255)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    uid: UUID = Field(default_factory=uuid4)

    # Content
    format: PromptFormat
    template: PromptTemplate | None = None
    chat_template: ChatPromptTemplate | None = None

    # Lifecycle
    status: PromptStatus = PromptStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    metadata: PromptMetadata = Field(default_factory=PromptMetadata)

    # Schema validation (optional)
    input_schema: str | None = Field(None, description="Name of input validation schema")
    output_schema: str | None = Field(None, description="Name of output validation schema")

    # Internal - injected by PromptManager (uses PrivateAttr for Pydantic compatibility)
    _schema_loader: Any = PrivateAttr(default=None)

    @model_validator(mode="after")
    def validate_template_format(self) -> "Prompt":
        """Validate that template matches format."""
        if self.format == PromptFormat.CHAT:
            if not self.chat_template:
                msg = "Chat format requires chat_template"
                raise ValueError(msg)
            if self.template:
                msg = "Chat format cannot have both template and chat_template"
                raise ValueError(msg)
        else:
            if not self.template:
                msg = f"{self.format} format requires template"
                raise ValueError(msg)
            if self.chat_template:
                msg = f"{self.format} format cannot have chat_template"
                raise ValueError(msg)
        return self

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Validate semantic versioning format."""
        parts = v.split(".")
        if len(parts) != 3:  # noqa: PLR2004
            msg = "Version must be in semver format (major.minor.patch)"
            raise ValueError(msg)
        if not all(p.isdigit() for p in parts):
            msg = "Version parts must be integers"
            raise ValueError(msg)
        return v

    def bump_version(self, level: Literal["major", "minor", "patch"] = "patch") -> str:
        """
        Bump version number.

        Args:
            level: Which part of version to bump

        Returns:
            New version string
        """
        major, minor, patch = map(int, self.version.split("."))

        if level == "major":
            major += 1
            minor = 0
            patch = 0
        elif level == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        new_version = f"{major}.{minor}.{patch}"
        self.version = new_version
        self.updated_at = datetime.utcnow()
        return new_version

    def get_variables(self) -> list[str]:
        """Get all template variables."""
        if self.template:
            return self.template.variables
        if self.chat_template:
            return self.chat_template.variables
        return []

    def render(
        self,
        variables: dict[str, Any],
        *,
        validate_input: bool = True,
        inject_schemas: bool = True,
        schema_loader: Any = None,
    ) -> str:
        """
        Render the prompt with provided variables.

        Full-featured rendering with validation and schema injection, matching
        PromptManager.render() capabilities. This method:
        - Validates input against input_schema (if defined and validate_input=True)
        - Injects output_schema descriptions (if defined and inject_schemas=True)
        - Provides clear error messages for missing variables

        Args:
            variables: Dictionary of variables to substitute
            validate_input: Whether to validate input against input_schema (default: True)
            inject_schemas: Whether to inject output schema descriptions (default: True)
            schema_loader: Optional SchemaLoader instance (auto-created if needed for validation)

        Returns:
            Rendered prompt string

        Raises:
            TemplateError: If rendering fails
            ValueError: If prompt has no template
            SchemaValidationError: If input validation fails

        Example:
            >>> # Simple rendering
            >>> prompt = pm.get_prompt("greeting")
            >>> result = prompt.render({"name": "Alice", "role": "Developer"})
            >>>
            >>> # Rendering with validation
            >>> result = prompt.render(
            ...     {"text": "...", "max_length": 100, "style": "bullet_points"},
            ...     validate_input=True
            ... )
        """
        # Validate input if schema is defined
        validated_vars = variables
        if validate_input and self.input_schema:
            # Use provided schema_loader, or injected one, or create new
            loader = schema_loader or self._schema_loader
            if loader is None:
                # Import and create default schema loader
                from prompt_manager.validation.loader import SchemaLoader
                loader = SchemaLoader()

            validated_vars = loader.validate_data(
                self.input_schema,
                dict(variables)
            )

        # Render based on format
        if self.format == PromptFormat.CHAT:
            rendered = self._render_chat(validated_vars)
        else:
            rendered = self._render_text(validated_vars)

        # Inject schema descriptions if requested
        if inject_schemas:
            # Use provided schema_loader, or injected one, or None
            loader = schema_loader or self._schema_loader
            rendered = self._inject_schema_descriptions(rendered, loader)

        return rendered

    def _inject_schema_descriptions(self, content: str, schema_loader: Any = None) -> str:
        """
        Inject output schema descriptions into rendered content.

        Args:
            content: Rendered content
            schema_loader: Optional schema loader (created if needed)

        Returns:
            Content with schema descriptions injected
        """
        if not self.output_schema:
            return content

        # Get schema
        if schema_loader is None:
            from prompt_manager.validation.loader import SchemaLoader
            schema_loader = SchemaLoader()

        schema = schema_loader.get_schema(self.output_schema)
        if not schema:
            # Schema not loaded - return content without injection
            return content

        # Format schema description
        lines = ["", "# Output Requirements", ""]
        lines.append("You MUST respond with valid JSON matching this exact structure:")
        lines.append("")

        if schema.description:
            lines.append(schema.description)
            lines.append("")

        lines.append("Required JSON format:")
        lines.append("```json")
        lines.append("{")

        # Build JSON example
        for i, field in enumerate(schema.fields):
            required = "required" if field.required else "optional"
            desc = field.description or "No description"

            # Format based on type
            if field.type == "string":
                example = f'  "{field.name}": "your {field.name} here"'
            elif field.type == "integer":
                example = f'  "{field.name}": 0'
            elif field.type == "float":
                example = f'  "{field.name}": 0.0'
            elif field.type == "boolean":
                example = f'  "{field.name}": true'
            elif field.type == "list":
                example = f'  "{field.name}": []'
            elif field.type == "dict":
                example = f'  "{field.name}": {{}}'
            else:
                example = f'  "{field.name}": null'

            example += f'  // {required} - {desc}'
            if i < len(schema.fields) - 1:
                example += ","

            lines.append(example)

        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("IMPORTANT: Return ONLY the JSON object, no additional text or explanation.")

        return content + "\n\n" + "\n".join(lines)

    def _render_text(self, variables: dict[str, Any]) -> str:
        """Render text-based prompt."""
        if not self.template:
            msg = f"Prompt {self.id} missing template"
            raise ValueError(msg)

        # Import here to avoid circular dependency
        from prompt_manager.core.template import TemplateEngine

        engine = TemplateEngine()
        return engine.render(
            self.template.content,
            variables,
            partials=self.template.partials,
        )

    def _render_chat(self, variables: dict[str, Any]) -> str:
        """Render chat-based prompt as formatted string."""
        if not self.chat_template:
            msg = f"Prompt {self.id} missing chat_template"
            raise ValueError(msg)

        # Import here to avoid circular dependency
        from prompt_manager.core.template import ChatTemplateEngine

        engine = ChatTemplateEngine()
        messages = [msg.model_dump() for msg in self.chat_template.messages]
        rendered_messages: list[dict[str, Any]] = engine.render_messages(messages, variables)

        # Format as string
        parts = []
        for msg in rendered_messages:  # type: ignore[assignment]
            role = msg["role"]  # type: ignore[index]
            content = msg["content"]  # type: ignore[index]
            parts.append(f"{role}: {content}")

        return "\n\n".join(parts)


class PromptVersion(BaseModel):
    """
    Represents a specific version of a prompt with changelog.

    Used for version history tracking.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt: Prompt
    version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = None
    changelog: str | None = None
    parent_version: str | None = None
    checksum: str | None = None

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Validate semantic versioning format."""
        parts = v.split(".")
        if len(parts) != 3:  # noqa: PLR2004
            msg = "Version must be in semver format (major.minor.patch)"
            raise ValueError(msg)
        if not all(p.isdigit() for p in parts):
            msg = "Version parts must be integers"
            raise ValueError(msg)
        return v


class PromptExecution(BaseModel):
    """Record of a prompt execution for observability."""

    model_config = ConfigDict(frozen=True, extra="allow")

    execution_id: UUID = Field(default_factory=uuid4)
    prompt_id: str
    prompt_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    variables: dict[str, Any]
    rendered_content: str
    success: bool
    duration_ms: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptSchema(BaseModel):
    """
    YAML schema definition for prompts.

    Allows defining prompts in YAML files with validation.
    """

    model_config = ConfigDict(extra="forbid")

    prompts: list[Prompt]
    version: str = "1.0.0"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("prompts")
    @classmethod
    def prompts_not_empty(cls, v: list[Prompt]) -> list[Prompt]:
        """Validate at least one prompt exists."""
        if not v:
            msg = "Schema must contain at least one prompt"
            raise ValueError(msg)
        return v

    @field_validator("prompts")
    @classmethod
    def unique_prompt_ids(cls, v: list[Prompt]) -> list[Prompt]:
        """Validate prompt IDs are unique within schema."""
        ids = [p.id for p in v]
        if len(ids) != len(set(ids)):
            msg = "Prompt IDs must be unique within schema"
            raise ValueError(msg)
        return v
