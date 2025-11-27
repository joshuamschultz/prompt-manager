"""
Main prompt manager orchestrating all components.

Provides high-level API for prompt management, rendering, and observability.
"""

import time
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from prompt_manager.core.models import (
    Message,
    Prompt,
    PromptExecution,
    PromptFormat,
    PromptStatus,
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
        registry: PromptRegistry | None = None,
        version_store: VersionStore | None = None,
        cache: CacheProtocol | None = None,
        metrics: MetricsCollectorProtocol | None = None,
        observers: list[ObserverProtocol] | None = None,
    ) -> None:
        """
        Initialize the prompt manager.

        Args:
            registry: Optional prompt registry (will create default if None)
            version_store: Optional version store for history
            cache: Optional cache for rendered prompts
            metrics: Optional metrics collector
            observers: Optional list of observers
        """
        # Create default registry if not provided
        if registry is None:
            from prompt_manager.storage import FileSystemStorage

            default_storage = FileSystemStorage(Path("./prompts"))
            registry = PromptRegistry(storage=default_storage)

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

    @classmethod
    def create(
        cls,
        prompt_dir: Path | str = "./prompts",
        auto_load_yaml: bool = True,
        version_store: VersionStore | None = None,
        cache: CacheProtocol | None = None,
        metrics: MetricsCollectorProtocol | None = None,
        observers: list[ObserverProtocol] | None = None,
    ) -> "PromptManager":
        """
        Create and initialize a PromptManager with auto-configuration.

        This is the recommended way to create a PromptManager. It:
        1. Creates storage in the specified prompt directory
        2. Automatically loads all YAML prompt files from that directory
        3. Auto-discovers and loads schemas for prompts that reference them
        4. Sets up all components with sensible defaults

        Args:
            prompt_dir: Directory for storing prompts (default: "./prompts")
            auto_load_yaml: Whether to auto-load YAML files (default: True)
            version_store: Optional version store for history
            cache: Optional cache for rendered prompts
            metrics: Optional metrics collector
            observers: Optional list of observers

        Returns:
            Initialized PromptManager instance

        Example:
            >>> # Simplest usage - everything automatic
            >>> manager = PromptManager.create()
            >>>
            >>> # Custom directory
            >>> manager = PromptManager.create(prompt_dir="./my-prompts")
            >>>
            >>> # Disable auto-loading
            >>> manager = PromptManager.create(auto_load_yaml=False)
        """
        from prompt_manager.storage import FileSystemStorage

        # Convert to Path if string
        if isinstance(prompt_dir, str):
            prompt_dir = Path(prompt_dir)

        # Create storage and registry
        storage = FileSystemStorage(prompt_dir)
        registry = PromptRegistry(storage=storage, observers=observers)

        # Create manager
        manager = cls(
            registry=registry,
            version_store=version_store,
            cache=cache,
            metrics=metrics,
            observers=observers,
        )

        # Auto-load YAML files if requested
        if auto_load_yaml and prompt_dir.exists():
            # Find all YAML files in the prompt directory (not in subdirectories)
            yaml_files = list(prompt_dir.glob("*.yaml")) + list(prompt_dir.glob("*.yml"))

            total_loaded = 0
            schemas_to_load: set[str] = set()

            for yaml_file in yaml_files:
                try:
                    # Load YAML file directly as a Prompt
                    import yaml

                    with open(yaml_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    # Validate and create Prompt
                    prompt = Prompt.model_validate(data)

                    # Register the prompt (don't persist since it's already on disk)
                    registry.register(prompt, persist=False)
                    total_loaded += 1

                    # Track schemas that need to be loaded
                    if prompt.input_schema:
                        schemas_to_load.add(prompt.input_schema)
                    if prompt.output_schema:
                        schemas_to_load.add(prompt.output_schema)

                    manager._logger.info(
                        "yaml_prompt_loaded",
                        file=str(yaml_file),
                        prompt_id=prompt.id,
                        version=prompt.version,
                    )

                except Exception as e:
                    manager._logger.warning(
                        "yaml_load_failed",
                        file=str(yaml_file),
                        error=str(e),
                    )

            if total_loaded > 0:
                manager._logger.info(
                    "yaml_loading_complete",
                    total_prompts=total_loaded,
                    total_files=len(yaml_files),
                )

            # Auto-discover and load schemas
            if schemas_to_load:
                manager._auto_load_schemas(prompt_dir, schemas_to_load)

        return manager

    def _auto_load_schemas(self, prompt_dir: Path, schema_names: set[str]) -> None:
        """
        Auto-discover and load schemas referenced by prompts.

        Looks for schemas in:
        1. {prompt_dir}/schemas/{schema_name}.yaml
        2. {prompt_dir}/../schemas/{schema_name}.yaml

        Args:
            prompt_dir: Prompt directory
            schema_names: Set of schema names to load
        """
        # Possible schema directories
        schema_dirs = [
            prompt_dir / "schemas",  # prompts/schemas/
            prompt_dir.parent / "schemas",  # examples/schemas/ (if prompt_dir is examples/prompts/)
        ]

        loaded_schemas: set[str] = set()

        for schema_name in schema_names:
            for schema_dir in schema_dirs:
                if not schema_dir.exists():
                    continue

                # Try .yaml and .yml extensions
                schema_files = [
                    schema_dir / f"{schema_name}.yaml",
                    schema_dir / f"{schema_name}.yml",
                ]

                for schema_file in schema_files:
                    if schema_file.exists() and schema_name not in loaded_schemas:
                        try:
                            registry = self._schema_loader.load_file(schema_file)
                            loaded_schemas.add(schema_name)

                            self._logger.info(
                                "schema_auto_loaded",
                                schema_name=schema_name,
                                file=str(schema_file),
                                schema_count=len(registry.schemas),
                            )
                            break  # Found and loaded, no need to check other paths

                        except Exception as e:
                            self._logger.warning(
                                "schema_auto_load_failed",
                                schema_name=schema_name,
                                file=str(schema_file),
                                error=str(e),
                            )

                if schema_name in loaded_schemas:
                    break  # Schema loaded, no need to check other directories

        # Warn about schemas that couldn't be loaded
        missing_schemas = schema_names - loaded_schemas
        if missing_schemas:
            self._logger.warning(
                "schemas_not_found",
                missing_schemas=list(missing_schemas),
                searched_dirs=[str(d) for d in schema_dirs],
            )

    def render_and_parse(
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

        Example:
            >>> manager = PromptManager()
            >>> result = manager.render_and_parse("greeting", {"name": "Alice"}, response_json)
        """
        # Get prompt to check for output schema
        prompt = self._registry.get(prompt_id, version)

        # Render with input validation (returns string for LLM)
        _ = self.render(prompt_id, variables, version=version, validate_input=True)

        # Parse response if it's a string
        if isinstance(llm_response, str):
            import json
            llm_response = json.loads(llm_response)

        # Validate output if schema defined (updated to use new API)
        if prompt.output_schema:
            return self.validate_output(prompt_id, llm_response, version=version)  # type: ignore[arg-type]

        return llm_response  # type: ignore[return-value]

    def validate_output(
        self,
        prompt_id: str,
        output_data: dict[str, Any],
        *,
        version: str | None = None,
    ) -> dict[str, Any]:
        """
        Validate LLM output against prompt's output schema.

        This method automatically looks up the output schema from the prompt definition,
        removing the need for users to know schema names.

        Args:
            prompt_id: ID of the prompt (uses its output_schema field)
            output_data: LLM output to validate
            version: Optional specific version of prompt

        Returns:
            Validated data

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            ValueError: If prompt has no output_schema defined
            SchemaValidationError: If validation fails

        Example:
            >>> # Simple - just pass prompt_id
            >>> validated = manager.validate_output("text_summarization", llm_response)
            >>>
            >>> # With specific version
            >>> validated = manager.validate_output("text_summarization", llm_response, version="1.0.0")
        """
        # 1. Get the prompt to find its output_schema
        prompt = self.get_prompt(prompt_id, version=version)

        # 2. Check that it has an output_schema defined
        if not prompt.output_schema:
            msg = (
                f"Prompt '{prompt_id}' has no output_schema defined. "
                f"Cannot validate output without a schema. "
                f"Add an output_schema field to the prompt YAML file."
            )
            raise ValueError(msg)

        # 3. Validate that the schema is actually loaded
        schema = self._schema_loader.get_schema(prompt.output_schema)
        if not schema:
            msg = (
                f"Output schema '{prompt.output_schema}' referenced by prompt '{prompt_id}' is not loaded. "
                f"Ensure the schema file exists in the schemas/ directory and has been loaded."
            )
            from prompt_manager.exceptions import SchemaValidationError
            raise SchemaValidationError(msg, schema=prompt.output_schema)

        # 4. Log and validate using the schema name
        self._logger.info(
            "validating_output",
            prompt_id=prompt_id,
            schema=prompt.output_schema,
            version=prompt.version,
        )

        validated = self._schema_loader.validate_data(prompt.output_schema, output_data)

        self._logger.info(
            "output_validated",
            prompt_id=prompt_id,
            schema=prompt.output_schema,
        )

        return validated

    def load_schemas(self, schema_path: Path) -> int:
        """
        Load validation schemas from a file or directory.

        Args:
            schema_path: Path to schema file or directory

        Returns:
            Number of schemas loaded

        Raises:
            SchemaParseError: If loading fails
            ValueError: If schema path does not exist

        Example:
            >>> count = manager.load_schemas(Path("schemas/user.json"))
        """
        self._logger.info("loading_schemas", path=str(schema_path))

        if schema_path.is_file():
            registry = self._schema_loader.load_file(schema_path)
            return len(registry.schemas)
        elif schema_path.is_dir():
            registries = self._schema_loader.load_directory(schema_path)
            total = sum(len(reg.schemas) for reg in registries)
            return total
        else:
            msg = f"Schema path does not exist: {schema_path}"
            raise ValueError(msg)

    def create_prompt(
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

        Example:
            >>> prompt = Prompt(...)
            >>> result = manager.create_prompt(prompt)
        """
        self._logger.info(
            "creating_prompt",
            prompt_id=prompt.id,
            version=prompt.version,
        )

        # Register in registry
        self._registry.register(prompt)

        # Create version record
        if self._version_store:
            version = PromptVersion(
                prompt=prompt,
                version=prompt.version,
                created_by=created_by,
                changelog=changelog,
            )
            self._version_store.save_version(version)

            # Notify observers
            for observer in self._observers:
                observer.on_version_created(version)

        return prompt

    def get_prompt(
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
            Requested prompt with schema_loader injected

        Raises:
            PromptNotFoundError: If prompt not found

        Example:
            >>> prompt = manager.get_prompt("greeting")
        """
        prompt = self._registry.get(prompt_id, version)
        # Inject schema loader so prompt.render() can use it
        prompt._schema_loader = self._schema_loader
        return prompt

    def update_prompt(
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

        Example:
            >>> updated_prompt = manager.update_prompt(prompt)
        """
        self._logger.info(
            "updating_prompt",
            prompt_id=prompt.id,
            version=prompt.version,
            bump_version=bump_version,
        )

        # Get current version for parent tracking
        try:
            current = self._registry.get(prompt.id)
            parent_version = current.version
        except PromptError:
            parent_version = None

        # Bump version if requested
        if bump_version:
            prompt.bump_version()

        # Update in registry
        self._registry.register(prompt)

        # Create version record
        if self._version_store:
            version = PromptVersion(
                prompt=prompt,
                version=prompt.version,
                created_by=created_by,
                changelog=changelog,
                parent_version=parent_version,
            )
            self._version_store.save_version(version)

            # Notify observers
            for observer in self._observers:
                observer.on_version_created(version)

        # Invalidate cache
        if self._cache:
            self._cache.invalidate(f"prompt:{prompt.id}:*")

        return prompt

    def render(
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

        Example:
            >>> manager = PromptManager()
            >>> result = manager.render("greeting", {"name": "Alice"})
        """
        start_time = time.perf_counter()

        # Get prompt
        prompt = self._registry.get(prompt_id, version)
        version = prompt.version

        # Auto-validate input if schema is defined
        if validate_input and prompt.input_schema:
            self._logger.debug("validating_input", schema=prompt.input_schema)
            variables = self._schema_loader.validate_data(
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
            observer.on_render_start(prompt_id, version, variables)

        # Check cache
        cache_key = self._make_cache_key(prompt_id, version, variables)
        if use_cache and self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                if self._metrics:
                    self._metrics.record_cache_hit(prompt_id)
                self._logger.debug("cache_hit", prompt_id=prompt_id)
                return cached

            if self._metrics:
                self._metrics.record_cache_miss(prompt_id)

        # Render based on format
        try:
            if prompt.format == PromptFormat.CHAT:
                rendered = self._render_chat(prompt, variables)
            else:
                rendered = self._render_text(prompt, variables)

            # Cache result
            if use_cache and self._cache:
                self._cache.set(cache_key, rendered)

            # Record metrics
            duration_ms = (time.perf_counter() - start_time) * 1000
            if self._metrics:
                self._metrics.record_render(
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
                observer.on_render_complete(prompt_id, version, execution)

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
                self._metrics.record_render(
                    prompt_id,
                    version,
                    duration_ms,
                    success=False,
                )

            # Notify observers
            for observer in self._observers:
                observer.on_render_error(prompt_id, version, e)

            self._logger.error(
                "render_failed",
                prompt_id=prompt_id,
                version=version,
                error=str(e),
            )

            raise

    def _render_text(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> str:
        """Render text-based prompt with optional schema injection."""
        if not prompt.template:
            msg = f"Prompt {prompt.id} missing template"
            raise TemplateError(msg)

        # Render the main content
        content = self._template_engine.render(
            prompt.template.content,
            variables,
            partials=prompt.template.partials,
        )

        # Inject schema descriptions if present
        return self._inject_schema_descriptions(prompt, content)

    def _inject_schema_descriptions(
        self,
        prompt: Prompt,
        content: str,
    ) -> str:
        """
        Inject output schema descriptions into rendered content.

        Note: Input schemas are for VALIDATION ONLY and should never appear in the prompt.
        This prevents token waste and ensures clean prompt output.

        Output schemas are injected to guide LLM responses with structured output requirements.
        """
        parts = []

        # REMOVED: Input schema injection (Issue #1)
        # Input schemas should ONLY validate input variables, never appear in rendered output.
        # This was previously adding unnecessary tokens to prompts sent to LLMs.

        # Add main content
        parts.append(content)

        # Add output schema description as ending (Issue #2: Added validation)
        if prompt.output_schema:
            # Validate that the schema is actually loaded before attempting to use it
            schema = self._schema_loader.get_schema(prompt.output_schema)
            if not schema:
                msg = (
                    f"Output schema '{prompt.output_schema}' is defined but not loaded. "
                    f"Please load the schema using manager.load_schemas() before rendering."
                )
                raise PromptError(msg)

            ending = self._format_output_schema_description(schema)
            parts.append(ending)

        return "\n\n".join(parts)

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

    def _render_chat(
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
        rendered_messages = self._chat_template_engine.render_messages(
            messages,
            variables,
        )

        # Format as string
        parts = []
        for msg in rendered_messages:  # type: ignore[assignment]
            role = msg["role"]  # type: ignore[index]
            content = msg["content"]  # type: ignore[index]
            parts.append(f"{role}: {content}")

        formatted_chat = "\n\n".join(parts)

        # Inject schema descriptions if present
        return self._inject_schema_descriptions(prompt, formatted_chat)

    def render_for_plugin(
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

        Example:
            >>> manager = PromptManager()
            >>> result = manager.render_for_plugin("greeting", {"name": "Alice"}, "openai")
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            from prompt_manager.exceptions import PluginNotFoundError

            raise PluginNotFoundError(plugin_name)

        prompt = self._registry.get(prompt_id, version)
        return plugin.render_for_framework(prompt, variables)

    def list_prompts(
        self,
        *,
        tags: list[str] | None = None,
        status: PromptStatus | None = None,
        category: str | None = None,
        format: PromptFormat | None = None,
    ) -> list[Prompt]:
        """
        List prompts with filtering.

        Args:
            tags: Filter by tags
            status: Filter by status
            category: Filter by category
            format: Filter by format

        Returns:
            List of matching prompts

        Example:
            >>> prompts = manager.list_prompts(tags=["greeting"])
            >>> text_prompts = manager.list_prompts(format=PromptFormat.TEXT)
        """
        return self._registry.list(
            tags=tags,
            status=status,
            category=category,
            format=format,
        )

    def get_history(
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

        Example:
            >>> history = manager.get_history("greeting")
        """
        if not self._version_store:
            return []

        return self._version_store.get_history(
            prompt_id,
            since=since,
            until=until,
        )

    def compare_versions(
        self,
        prompt_id: str,
        version1: str,
        version2: str,
    ) -> dict[str, Any]:
        """
        Compare two versions and return differences.

        Args:
            prompt_id: Prompt identifier
            version1: First version (older)
            version2: Second version (newer)

        Returns:
            Dictionary of differences with keys:
            - versions: {"from": version1, "to": version2}
            - checksums_differ: bool
            - status_changed: bool
            - template_changed: bool
            - metadata_changed: bool

        Raises:
            PromptNotFoundError: If prompt not found
            VersionNotFoundError: If either version doesn't exist

        Example:
            >>> diff = manager.compare_versions("greeting", "1.0.0", "1.0.1")
            >>> print(diff["versions"])  # {"from": "1.0.0", "to": "1.0.1"}
        """
        if not self._version_store:
            return {
                "versions": {"from": version1, "to": version2},
                "error": "No version store configured",
            }

        return self._version_store.compare_versions(prompt_id, version1, version2)

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

    def get_metrics(
        self,
        *,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get system metrics.

        Args:
            since: Only metrics after this time

        Returns:
            Metrics dictionary containing registry stats and optional operation metrics

        Example:
            >>> metrics = manager.get_metrics()
        """
        metrics = {
            "registry": self._registry.get_stats(),
        }

        if self._metrics:
            metrics["operations"] = self._metrics.get_metrics(since=since)

        return metrics
