"""
Main prompt manager orchestrating all components.

Provides high-level API for prompt management, rendering, and observability.
"""

import time
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog

from prompt_manager.core.models import (
    Message,
    Prompt,
    PromptExecution,
    PromptFormat,
    PromptVersion,
)
from prompt_manager.core.protocols import (
    CacheProtocol,
    MetricsCollectorProtocol,
    ObserverProtocol,
    PluginProtocol,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.core.template import ChatTemplateEngine, TemplateEngine
from prompt_manager.exceptions import PromptError, TemplateError
from prompt_manager.validation.loader import SchemaLoader
from prompt_manager.versioning.store import VersionStore

logger = structlog.get_logger(__name__)


class PromptManager:
    """
    Main entry point for the prompt management system.

    Orchestrates registry, templating, versioning, caching, and observability.
    """

    def __init__(
        self,
        registry: PromptRegistry,
        version_store: VersionStore | None = None,
        cache: CacheProtocol | None = None,
        metrics: MetricsCollectorProtocol | None = None,
        observers: list[ObserverProtocol] | None = None,
    ) -> None:
        """
        Initialize the prompt manager.

        Args:
            registry: Prompt registry for storage
            version_store: Optional version store for history
            cache: Optional cache for rendered prompts
            metrics: Optional metrics collector
            observers: Optional list of observers
        """
        self._registry = registry
        self._version_store = version_store
        self._cache = cache
        self._metrics = metrics
        self._observers = observers or []

        self._template_engine = TemplateEngine()
        self._chat_template_engine = ChatTemplateEngine()
        self._plugins: dict[str, PluginProtocol] = {}
        self._schema_loader = SchemaLoader()

        self._logger = logger.bind(component="manager")

    async def render_and_parse(
        self,
        prompt_id: str,
        variables: Mapping[str, Any],
        llm_response: dict[str, Any] | str,
        *,
        version: str | None = None,
    ) -> dict[str, Any]:
        """
        Complete validation flow: validates input, renders prompt, validates output.

        This is a convenience method that combines:
        1. Input validation (automatic if input_schema defined)
        2. Prompt rendering with schema injection
        3. Output validation (automatic if output_schema defined)

        Args:
            prompt_id: Prompt identifier
            variables: Input variables
            llm_response: LLM response to validate (dict or JSON string)
            version: Optional version

        Returns:
            Validated output data

        Raises:
            SchemaValidationError: If input or output validation fails
            PromptNotFoundError: If prompt not found
        """
        # Get prompt to check for output schema
        prompt = await self._registry.get(prompt_id, version)

        # Render with input validation (returns string for LLM)
        _ = await self.render(prompt_id, variables, version=version, validate_input=True)

        # Parse response if it's a string
        if isinstance(llm_response, str):
            import json
            llm_response = json.loads(llm_response)

        # Validate output if schema defined
        if prompt.output_schema:
            return await self.validate_output(prompt.output_schema, llm_response)

        return llm_response

    async def validate_output(
        self,
        schema_name: str,
        output_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate LLM output against a schema.

        Args:
            schema_name: Name of the output schema
            output_data: LLM output to validate

        Returns:
            Validated data

        Raises:
            SchemaValidationError: If validation fails
        """
        self._logger.info("validating_output", schema=schema_name)

        validated = await self._schema_loader.validate_data(schema_name, output_data)

        self._logger.info("output_validated", schema=schema_name)
        return validated

    async def load_schemas(self, schema_path: Path) -> int:
        """
        Load validation schemas from a file or directory.

        Args:
            schema_path: Path to schema file or directory

        Returns:
            Number of schemas loaded

        Raises:
            SchemaParseError: If loading fails
        """
        self._logger.info("loading_schemas", path=str(schema_path))

        if schema_path.is_file():
            registry = await self._schema_loader.load_file(schema_path)
            return len(registry.schemas)
        elif schema_path.is_dir():
            registries = await self._schema_loader.load_directory(schema_path)
            total = sum(len(reg.schemas) for reg in registries)
            return total
        else:
            msg = f"Schema path does not exist: {schema_path}"
            raise ValueError(msg)

    async def create_prompt(
        self,
        prompt: Prompt,
        *,
        changelog: str | None = None,
        created_by: str | None = None,
    ) -> Prompt:
        """
        Create a new prompt with version tracking.

        Args:
            prompt: Prompt to create
            changelog: Optional changelog entry
            created_by: Optional creator identifier

        Returns:
            Created prompt

        Raises:
            PromptValidationError: If prompt is invalid
        """
        self._logger.info(
            "creating_prompt",
            prompt_id=prompt.id,
            version=prompt.version,
        )

        # Register in registry
        await self._registry.register(prompt)

        # Create version record
        if self._version_store:
            version = PromptVersion(
                prompt=prompt,
                version=prompt.version,
                created_by=created_by,
                changelog=changelog,
            )
            await self._version_store.save_version(version)

            # Notify observers
            for observer in self._observers:
                await observer.on_version_created(version)

        return prompt

    async def get_prompt(
        self,
        prompt_id: str,
        version: str | None = None,
    ) -> Prompt:
        """
        Get a prompt by ID and optional version.

        Args:
            prompt_id: Prompt identifier
            version: Optional version (gets latest if None)

        Returns:
            Requested prompt

        Raises:
            PromptNotFoundError: If prompt not found
        """
        return await self._registry.get(prompt_id, version)

    async def update_prompt(
        self,
        prompt: Prompt,
        *,
        bump_version: bool = True,
        changelog: str | None = None,
        created_by: str | None = None,
    ) -> Prompt:
        """
        Update a prompt, optionally creating a new version.

        Args:
            prompt: Updated prompt
            bump_version: Whether to bump version number
            changelog: Optional changelog entry
            created_by: Optional updater identifier

        Returns:
            Updated prompt

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        self._logger.info(
            "updating_prompt",
            prompt_id=prompt.id,
            version=prompt.version,
            bump_version=bump_version,
        )

        # Get current version for parent tracking
        try:
            current = await self._registry.get(prompt.id)
            parent_version = current.version
        except PromptError:
            parent_version = None

        # Bump version if requested
        if bump_version:
            prompt.bump_version()

        # Update in registry
        await self._registry.register(prompt)

        # Create version record
        if self._version_store:
            version = PromptVersion(
                prompt=prompt,
                version=prompt.version,
                created_by=created_by,
                changelog=changelog,
                parent_version=parent_version,
            )
            await self._version_store.save_version(version)

            # Notify observers
            for observer in self._observers:
                await observer.on_version_created(version)

        # Invalidate cache
        if self._cache:
            await self._cache.invalidate(f"prompt:{prompt.id}:*")

        return prompt

    async def render(
        self,
        prompt_id: str,
        variables: Mapping[str, Any],
        *,
        version: str | None = None,
        use_cache: bool = True,
        validate_input: bool = True,
        validate_output: bool = False,
    ) -> str | dict[str, Any]:
        """
        Render a prompt with variables.

        Args:
            prompt_id: Prompt identifier
            version: Optional version (uses latest if None)
            variables: Variables for rendering
            use_cache: Whether to use cache
            validate_input: Whether to validate input variables (default: True)
            validate_output: If True, returns validation-ready dict instead of string

        Returns:
            Rendered prompt string, or dict with prompt and schema info if validate_output=True

        Raises:
            PromptNotFoundError: If prompt not found
            TemplateError: If rendering fails
            SchemaValidationError: If input validation fails
        """
        start_time = time.perf_counter()

        # Get prompt
        prompt = await self._registry.get(prompt_id, version)
        version = prompt.version

        # Auto-validate input if schema is defined
        if validate_input and prompt.input_schema:
            self._logger.debug("validating_input", schema=prompt.input_schema)
            variables = await self._schema_loader.validate_data(
                prompt.input_schema,
                dict(variables)
            )

        self._logger.info(
            "rendering_prompt",
            prompt_id=prompt_id,
            version=version,
        )

        # Notify observers
        for observer in self._observers:
            await observer.on_render_start(prompt_id, version, variables)

        # Check cache
        cache_key = self._make_cache_key(prompt_id, version, variables)
        if use_cache and self._cache:
            cached = await self._cache.get(cache_key)
            if cached:
                if self._metrics:
                    await self._metrics.record_cache_hit(prompt_id)
                self._logger.debug("cache_hit", prompt_id=prompt_id)
                return cached

            if self._metrics:
                await self._metrics.record_cache_miss(prompt_id)

        # Render based on format
        try:
            if prompt.format == PromptFormat.CHAT:
                rendered = await self._render_chat(prompt, variables)
            else:
                rendered = await self._render_text(prompt, variables)

            # Cache result
            if use_cache and self._cache:
                await self._cache.set(cache_key, rendered)

            # Record metrics
            duration_ms = (time.perf_counter() - start_time) * 1000
            if self._metrics:
                await self._metrics.record_render(
                    prompt_id,
                    version,
                    duration_ms,
                    success=True,
                )

            # Create execution record
            execution = PromptExecution(
                prompt_id=prompt_id,
                prompt_version=version,
                variables=dict(variables),
                rendered_content=rendered,
                success=True,
                duration_ms=duration_ms,
            )

            # Notify observers
            for observer in self._observers:
                await observer.on_render_complete(prompt_id, version, execution)

            self._logger.info(
                "prompt_rendered",
                prompt_id=prompt_id,
                version=version,
                duration_ms=duration_ms,
            )

            # Return validation info if requested
            if validate_output and prompt.output_schema:
                return {
                    "prompt": rendered,
                    "output_schema": prompt.output_schema,
                    "prompt_id": prompt_id,
                    "version": version,
                }

            return rendered

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Record metrics
            if self._metrics:
                await self._metrics.record_render(
                    prompt_id,
                    version,
                    duration_ms,
                    success=False,
                )

            # Notify observers
            for observer in self._observers:
                await observer.on_render_error(prompt_id, version, e)

            self._logger.error(
                "render_failed",
                prompt_id=prompt_id,
                version=version,
                error=str(e),
            )

            raise

    async def _render_text(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> str:
        """Render text-based prompt with optional schema injection."""
        if not prompt.template:
            msg = f"Prompt {prompt.id} missing template"
            raise TemplateError(msg)

        # Render the main content
        content = await self._template_engine.render(
            prompt.template.content,
            variables,
            partials=prompt.template.partials,
        )

        # Inject schema descriptions if present
        return await self._inject_schema_descriptions(prompt, content)

    async def _inject_schema_descriptions(
        self,
        prompt: Prompt,
        content: str,
    ) -> str:
        """Inject input/output schema descriptions into rendered content."""
        parts = []

        # Add input schema description as intro
        if prompt.input_schema:
            schema = self._schema_loader.get_schema(prompt.input_schema)
            if schema:
                intro = self._format_input_schema_description(schema)
                parts.append(intro)

        # Add main content
        parts.append(content)

        # Add output schema description as ending
        if prompt.output_schema:
            schema = self._schema_loader.get_schema(prompt.output_schema)
            if schema:
                ending = self._format_output_schema_description(schema)
                parts.append(ending)

        return "\n\n".join(parts)

    def _format_input_schema_description(self, schema: Any) -> str:
        """Format input schema as description text."""
        lines = ["# Input Requirements", ""]
        if schema.description:
            lines.append(schema.description)
            lines.append("")

        lines.append("Expected input fields:")
        for field in schema.fields:
            required = "required" if field.required else "optional"
            desc = field.description or "No description"
            lines.append(f"- {field.name} ({field.type}, {required}): {desc}")

        return "\n".join(lines)

    def _format_output_schema_description(self, schema: Any) -> str:
        """Format output schema as description text with structured output instructions."""
        lines = ["# Output Requirements", ""]

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

            # Add comment
            example += f'  // {required} - {desc}'

            # Add comma if not last field
            if i < len(schema.fields) - 1:
                example += ","

            lines.append(example)

        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("IMPORTANT: Return ONLY the JSON object, no additional text or explanation.")

        return "\n".join(lines)

    async def _render_chat(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> str:
        """Render chat-based prompt as formatted string with optional schema injection."""
        if not prompt.chat_template:
            msg = f"Prompt {prompt.id} missing chat_template"
            raise TemplateError(msg)

        # Convert Message models to dicts
        messages = [msg.model_dump() for msg in prompt.chat_template.messages]

        # Render messages
        rendered_messages = await self._chat_template_engine.render_messages(
            messages,
            variables,
        )

        # Format as string
        parts = []
        for msg in rendered_messages:
            role = msg["role"]
            content = msg["content"]
            parts.append(f"{role}: {content}")

        formatted_chat = "\n\n".join(parts)

        # Inject schema descriptions if present
        return await self._inject_schema_descriptions(prompt, formatted_chat)

    async def render_for_plugin(
        self,
        prompt_id: str,
        variables: Mapping[str, Any],
        plugin_name: str,
        *,
        version: str | None = None,
    ) -> Any:
        """
        Render prompt using a specific plugin.

        Args:
            prompt_id: Prompt identifier
            variables: Variables for rendering
            plugin_name: Name of plugin to use
            version: Optional version

        Returns:
            Plugin-specific rendered format

        Raises:
            PluginNotFoundError: If plugin not found
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            from prompt_manager.exceptions import PluginNotFoundError

            raise PluginNotFoundError(plugin_name)

        prompt = await self._registry.get(prompt_id, version)
        return await plugin.render_for_framework(prompt, variables)

    async def list_prompts(
        self,
        *,
        tags: list[str] | None = None,
        status: str | None = None,
        category: str | None = None,
    ) -> list[Prompt]:
        """
        List prompts with filtering.

        Args:
            tags: Filter by tags
            status: Filter by status
            category: Filter by category

        Returns:
            List of matching prompts
        """
        return await self._registry.list(
            tags=tags,
            status=status,
            category=category,
        )

    async def get_history(
        self,
        prompt_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[PromptVersion]:
        """
        Get version history for a prompt.

        Args:
            prompt_id: Prompt identifier
            since: Only versions after this time
            until: Only versions before this time

        Returns:
            Version history

        Raises:
            PromptNotFoundError: If prompt not found
        """
        if not self._version_store:
            return []

        return await self._version_store.get_history(
            prompt_id,
            since=since,
            until=until,
        )

    def register_plugin(self, plugin: PluginProtocol) -> None:
        """
        Register a plugin for LLM framework integration.

        Args:
            plugin: Plugin to register
        """
        self._plugins[plugin.name] = plugin
        self._logger.info("plugin_registered", plugin=plugin.name)

    def add_observer(self, observer: ObserverProtocol) -> None:
        """
        Add an observer for lifecycle events.

        Args:
            observer: Observer to add
        """
        self._observers.append(observer)
        self._registry.add_observer(observer)

    @staticmethod
    def _make_cache_key(
        prompt_id: str,
        version: str,
        variables: Mapping[str, Any],
    ) -> str:
        """Create cache key from prompt and variables."""
        # Sort variables for consistent key
        var_str = "|".join(f"{k}={v}" for k, v in sorted(variables.items()))
        return f"prompt:{prompt_id}:{version}:{hash(var_str)}"

    async def get_metrics(
        self,
        *,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get system metrics.

        Args:
            since: Only metrics after this time

        Returns:
            Metrics dictionary
        """
        metrics = {
            "registry": await self._registry.get_stats(),
        }

        if self._metrics:
            metrics["operations"] = await self._metrics.get_metrics(since=since)

        return metrics
