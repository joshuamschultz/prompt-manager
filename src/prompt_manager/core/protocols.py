"""
Protocol definitions for core abstractions.

Uses Protocol for structural subtyping (duck typing with type safety).
This enables plugin architecture without tight coupling.
"""

from collections.abc import AsyncIterator, Mapping
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from prompt_manager.core.models import Prompt, PromptExecution, PromptVersion


@runtime_checkable
class TemplateEngineProtocol(Protocol):
    """Protocol for template rendering engines."""

    async def render(
        self,
        template: str,
        variables: Mapping[str, Any],
        *,
        partials: Mapping[str, str] | None = None,
    ) -> str:
        """
        Render a template with variables.

        Args:
            template: Template string
            variables: Variables for rendering
            partials: Optional partial templates

        Returns:
            Rendered string

        Raises:
            TemplateError: If rendering fails
        """
        ...

    async def validate(self, template: str) -> bool:
        """
        Validate template syntax.

        Args:
            template: Template string to validate

        Returns:
            True if valid

        Raises:
            TemplateSyntaxError: If template is invalid
        """
        ...

    def extract_variables(self, template: str) -> list[str]:
        """
        Extract variable names from template.

        Args:
            template: Template string

        Returns:
            List of variable names
        """
        ...


@runtime_checkable
class StorageBackendProtocol(Protocol):
    """Protocol for storage backends."""

    async def save(self, prompt: Prompt) -> None:
        """
        Save a prompt to storage.

        Args:
            prompt: Prompt to save

        Raises:
            StorageError: If save fails
        """
        ...

    async def load(self, prompt_id: str, version: str | None = None) -> Prompt:
        """
        Load a prompt from storage.

        Args:
            prompt_id: Prompt identifier
            version: Optional version (loads latest if None)

        Returns:
            Loaded prompt

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            StorageError: If load fails
        """
        ...

    async def delete(self, prompt_id: str, version: str | None = None) -> None:
        """
        Delete a prompt from storage.

        Args:
            prompt_id: Prompt identifier
            version: Optional version (deletes all if None)

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            StorageError: If delete fails
        """
        ...

    async def list(
        self,
        *,
        tags: list[str] | None = None,
        status: str | None = None,
    ) -> list[Prompt]:
        """
        List prompts matching filters.

        Args:
            tags: Filter by tags
            status: Filter by status

        Returns:
            List of matching prompts

        Raises:
            StorageError: If list fails
        """
        ...

    async def exists(self, prompt_id: str, version: str | None = None) -> bool:
        """
        Check if a prompt exists.

        Args:
            prompt_id: Prompt identifier
            version: Optional version

        Returns:
            True if exists
        """
        ...


@runtime_checkable
class VersionStoreProtocol(Protocol):
    """Protocol for version storage."""

    async def save_version(self, version: PromptVersion) -> None:
        """
        Save a prompt version.

        Args:
            version: Prompt version to save

        Raises:
            VersionError: If save fails
        """
        ...

    async def get_version(self, prompt_id: str, version: str) -> PromptVersion:
        """
        Get a specific version.

        Args:
            prompt_id: Prompt identifier
            version: Version string

        Returns:
            Prompt version

        Raises:
            VersionNotFoundError: If version doesn't exist
        """
        ...

    async def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        """
        List all versions for a prompt.

        Args:
            prompt_id: Prompt identifier

        Returns:
            List of versions, newest first

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        ...

    async def get_latest(self, prompt_id: str) -> PromptVersion:
        """
        Get the latest version.

        Args:
            prompt_id: Prompt identifier

        Returns:
            Latest version

        Raises:
            PromptNotFoundError: If no versions exist
        """
        ...

    async def get_history(
        self,
        prompt_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[PromptVersion]:
        """
        Get version history with time filters.

        Args:
            prompt_id: Prompt identifier
            since: Only versions after this time
            until: Only versions before this time

        Returns:
            Filtered version history

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        ...


@runtime_checkable
class ObserverProtocol(Protocol):
    """Protocol for observability hooks."""

    async def on_render_start(
        self,
        prompt_id: str,
        version: str,
        variables: Mapping[str, Any],
    ) -> None:
        """
        Called when prompt rendering starts.

        Args:
            prompt_id: Prompt identifier
            version: Version being rendered
            variables: Variables for rendering
        """
        ...

    async def on_render_complete(
        self,
        prompt_id: str,
        version: str,
        execution: PromptExecution,
    ) -> None:
        """
        Called when prompt rendering completes.

        Args:
            prompt_id: Prompt identifier
            version: Version that was rendered
            execution: Execution record
        """
        ...

    async def on_render_error(
        self,
        prompt_id: str,
        version: str,
        error: Exception,
    ) -> None:
        """
        Called when prompt rendering fails.

        Args:
            prompt_id: Prompt identifier
            version: Version that failed
            error: Exception that occurred
        """
        ...

    async def on_version_created(self, version: PromptVersion) -> None:
        """
        Called when a new version is created.

        Args:
            version: New version
        """
        ...


@runtime_checkable
class PluginProtocol(Protocol):
    """Protocol for LLM framework plugins."""

    name: str
    version: str

    async def initialize(self, config: Mapping[str, Any]) -> None:
        """
        Initialize the plugin.

        Args:
            config: Plugin configuration

        Raises:
            PluginError: If initialization fails
        """
        ...

    async def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> Any:
        """
        Render prompt in framework-specific format.

        Args:
            prompt: Prompt to render
            variables: Variables for rendering

        Returns:
            Framework-specific prompt format

        Raises:
            PlugptError: If rendering fails
        """
        ...

    async def validate_compatibility(self, prompt: Prompt) -> bool:
        """
        Check if prompt is compatible with framework.

        Args:
            prompt: Prompt to check

        Returns:
            True if compatible
        """
        ...

    async def shutdown(self) -> None:
        """Clean up plugin resources."""
        ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for caching rendered prompts."""

    async def get(
        self,
        key: str,
    ) -> str | None:
        """
        Get cached rendered prompt.

        Args:
            key: Cache key

        Returns:
            Cached content or None if not found
        """
        ...

    async def set(
        self,
        key: str,
        value: str,
        *,
        ttl: int | None = None,
    ) -> None:
        """
        Cache rendered prompt.

        Args:
            key: Cache key
            value: Content to cache
            ttl: Time to live in seconds
        """
        ...

    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (e.g., "prompt:*")

        Returns:
            Number of entries invalidated
        """
        ...

    async def clear(self) -> None:
        """Clear all cache entries."""
        ...


@runtime_checkable
class EventStreamProtocol(Protocol):
    """Protocol for event streaming."""

    async def publish(
        self,
        event_type: str,
        payload: Mapping[str, Any],
    ) -> None:
        """
        Publish an event.

        Args:
            event_type: Type of event
            payload: Event data
        """
        ...

    async def subscribe(
        self,
        event_type: str,
    ) -> AsyncIterator[Mapping[str, Any]]:
        """
        Subscribe to events of a type.

        Args:
            event_type: Type of event to subscribe to

        Yields:
            Event payloads
        """
        ...


@runtime_checkable
class MetricsCollectorProtocol(Protocol):
    """Protocol for metrics collection."""

    async def record_render(
        self,
        prompt_id: str,
        version: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """
        Record a render operation.

        Args:
            prompt_id: Prompt identifier
            version: Version rendered
            duration_ms: Duration in milliseconds
            success: Whether rendering succeeded
        """
        ...

    async def record_cache_hit(self, prompt_id: str) -> None:
        """Record a cache hit."""
        ...

    async def record_cache_miss(self, prompt_id: str) -> None:
        """Record a cache miss."""
        ...

    async def get_metrics(
        self,
        *,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get collected metrics.

        Args:
            since: Only metrics after this time

        Returns:
            Metrics dictionary
        """
        ...
