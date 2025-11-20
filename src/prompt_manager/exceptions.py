"""
Exception hierarchy for the prompt manager system.

All exceptions inherit from PromptManagerError for easy catching and handling.
"""

from typing import Any


class PromptManagerError(Exception):
    """Base exception for all prompt manager errors."""

    def __init__(self, message: str, **context: Any) -> None:
        """
        Initialize exception with message and optional context.

        Args:
            message: Error message
            **context: Additional context for debugging
        """
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self) -> str:
        """Return string representation with context."""
        if self.context:
            ctx_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} ({ctx_str})"
        return self.message


class PromptError(PromptManagerError):
    """Base exception for prompt-related errors."""


class PromptNotFoundError(PromptError):
    """Raised when a prompt cannot be found in the registry."""

    def __init__(self, prompt_id: str, version: str | None = None) -> None:
        """
        Initialize with prompt identifier.

        Args:
            prompt_id: The prompt identifier that was not found
            version: Optional version that was requested
        """
        msg = f"Prompt '{prompt_id}' not found"
        if version:
            msg += f" (version: {version})"
        super().__init__(msg, prompt_id=prompt_id, version=version)


class PromptValidationError(PromptError):
    """Raised when prompt validation fails."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        """
        Initialize with validation errors.

        Args:
            message: Error message
            errors: List of validation errors from Pydantic
        """
        super().__init__(message, errors=errors or [])
        self.errors = errors or []


class TemplateError(PromptManagerError):
    """Base exception for template-related errors."""


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""

    def __init__(self, template: str, variables: dict[str, Any], cause: Exception) -> None:
        """
        Initialize with template context.

        Args:
            template: The template that failed to render
            variables: Variables provided for rendering
            cause: The underlying exception
        """
        msg = f"Failed to render template: {cause}"
        super().__init__(msg, template=template, variables=variables, cause=str(cause))
        self.__cause__ = cause


class TemplateSyntaxError(TemplateError):
    """Raised when template has invalid syntax."""


class VersionError(PromptManagerError):
    """Base exception for versioning errors."""


class VersionNotFoundError(VersionError):
    """Raised when a specific version is not found."""

    def __init__(self, prompt_id: str, version: str) -> None:
        """
        Initialize with version information.

        Args:
            prompt_id: The prompt identifier
            version: The version that was not found
        """
        msg = f"Version '{version}' not found for prompt '{prompt_id}'"
        super().__init__(msg, prompt_id=prompt_id, version=version)


class VersionConflictError(VersionError):
    """Raised when there's a version conflict (e.g., concurrent updates)."""


class StorageError(PromptManagerError):
    """Base exception for storage-related errors."""


class StorageReadError(StorageError):
    """Raised when reading from storage fails."""


class StorageWriteError(StorageError):
    """Raised when writing to storage fails."""


class PluginError(PromptManagerError):
    """Base exception for plugin-related errors."""


class PluginNotFoundError(PluginError):
    """Raised when a plugin cannot be found."""

    def __init__(self, plugin_name: str) -> None:
        """
        Initialize with plugin name.

        Args:
            plugin_name: Name of the plugin that was not found
        """
        msg = f"Plugin '{plugin_name}' not found"
        super().__init__(msg, plugin_name=plugin_name)


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""


class PluginValidationError(PluginError):
    """Raised when a plugin fails validation."""


class SchemaError(PromptManagerError):
    """Base exception for schema-related errors."""


class SchemaValidationError(SchemaError):
    """Raised when schema validation fails."""


class SchemaParseError(SchemaError):
    """Raised when schema parsing fails."""


class IntegrationError(PromptManagerError):
    """Base exception for framework integration errors."""


class IntegrationNotAvailableError(IntegrationError):
    """Raised when a framework integration is used but dependencies are not installed."""

    def __init__(self, integration_name: str, extra: str | None = None) -> None:
        """
        Initialize with integration details and install instructions.

        Args:
            integration_name: Name of the integration (e.g., "openai", "langchain")
            extra: Optional pip extra name for installation
        """
        extra_name = extra or integration_name
        msg = (
            f"Integration '{integration_name}' is not available. "
            f"Install it with: pip install agentic-prompt-manager[{extra_name}]"
        )
        super().__init__(msg, integration_name=integration_name, extra=extra_name)


class ConversionError(IntegrationError):
    """Raised when prompt conversion to framework format fails."""

    def __init__(
        self,
        message: str,
        prompt_id: str | None = None,
        framework: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """
        Initialize with conversion context.

        Args:
            message: Error message describing the conversion failure
            prompt_id: Optional prompt identifier
            framework: Optional framework name
            cause: Optional underlying exception
        """
        super().__init__(
            message,
            prompt_id=prompt_id,
            framework=framework,
            cause=str(cause) if cause else None,
        )
        if cause:
            self.__cause__ = cause


class IncompatibleFormatError(IntegrationError):
    """Raised when prompt format is incompatible with the target framework."""

    def __init__(
        self,
        prompt_format: str,
        framework: str,
        supported_formats: list[str] | None = None,
    ) -> None:
        """
        Initialize with format compatibility information.

        Args:
            prompt_format: The prompt format that was attempted (e.g., "TEXT", "CHAT")
            framework: The target framework name
            supported_formats: Optional list of formats supported by the framework
        """
        msg = f"Prompt format '{prompt_format}' is incompatible with framework '{framework}'"
        if supported_formats:
            formats_str = ", ".join(supported_formats)
            msg += f". Supported formats: {formats_str}"
        super().__init__(
            msg,
            prompt_format=prompt_format,
            framework=framework,
            supported_formats=supported_formats,
        )


class ObservabilityError(PromptManagerError):
    """Base exception for observability-related errors."""


class TelemetryError(ObservabilityError):
    """Raised when telemetry operations fail."""


class TracingError(ObservabilityError):
    """Raised when tracing operations fail."""
