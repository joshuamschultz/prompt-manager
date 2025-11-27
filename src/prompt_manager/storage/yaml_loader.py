"""YAML loader for importing prompt schemas from files."""

from pathlib import Path

import structlog
import yaml

from prompt_manager.core.models import PromptSchema
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.exceptions import SchemaParseError, SchemaValidationError

logger = structlog.get_logger(__name__)


class YAMLLoader:
    """
    YAML loader for importing prompt schemas.

    Supports loading prompts from YAML files with validation.
    """

    def __init__(self, registry: PromptRegistry | None = None) -> None:
        """
        Initialize YAML loader.

        Args:
            registry: Optional registry to load prompts into
        """
        self._registry = registry
        self._logger = logger.bind(component="yaml_loader")

    def load_file(self, filepath: Path) -> PromptSchema:
        """
        Load and parse a YAML file.

        Args:
            filepath: Path to YAML file

        Returns:
            Parsed prompt schema

        Raises:
            SchemaParseError: If YAML parsing fails
            SchemaValidationError: If validation fails
        """
        self._logger.info("loading_yaml", file=str(filepath))

        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Parse YAML
            data = yaml.safe_load(content)

            if not data:
                msg = "Empty YAML file"
                raise SchemaParseError(msg, file=str(filepath))

            # Validate with Pydantic
            schema = PromptSchema.model_validate(data)

            self._logger.info(
                "yaml_loaded",
                file=str(filepath),
                prompt_count=len(schema.prompts),
            )

            return schema

        except yaml.YAMLError as e:
            msg = f"Invalid YAML syntax: {e}"
            raise SchemaParseError(msg, file=str(filepath)) from e
        except Exception as e:
            msg = f"Failed to validate schema: {e}"
            raise SchemaValidationError(msg, file=str(filepath)) from e

    def load_directory(self, dirpath: Path) -> list[PromptSchema]:
        """
        Load all YAML files from a directory.

        Args:
            dirpath: Directory path

        Returns:
            List of loaded schemas

        Raises:
            SchemaParseError: If any file fails to parse
        """
        self._logger.info("loading_directory", path=str(dirpath))

        schemas = []
        yaml_files = list(dirpath.glob("*.yaml")) + list(dirpath.glob("*.yml"))

        for filepath in yaml_files:
            try:
                schema = self.load_file(filepath)
                schemas.append(schema)
            except Exception as e:
                self._logger.error(
                    "failed_to_load_file",
                    file=str(filepath),
                    error=str(e),
                )
                # Continue with other files
                continue

        self._logger.info(
            "directory_loaded",
            path=str(dirpath),
            schema_count=len(schemas),
        )

        return schemas

    def import_to_registry(
        self,
        filepath: Path,
        *,
        registry: PromptRegistry | None = None,
    ) -> int:
        """
        Load YAML file and import prompts to registry.

        Args:
            filepath: Path to YAML file
            registry: Optional registry (uses instance registry if None)

        Returns:
            Number of prompts imported

        Raises:
            ValueError: If no registry available
            SchemaParseError: If parsing fails
        """
        target_registry = registry or self._registry
        if not target_registry:
            msg = "No registry available for import"
            raise ValueError(msg)

        schema = self.load_file(filepath)

        count = 0
        for prompt in schema.prompts:
            target_registry.register(prompt)
            count += 1

        self._logger.info(
            "prompts_imported",
            file=str(filepath),
            count=count,
        )

        return count

    def import_directory_to_registry(
        self,
        dirpath: Path,
        *,
        registry: PromptRegistry | None = None,
    ) -> int:
        """
        Load all YAML files from directory and import to registry.

        Args:
            dirpath: Directory path
            registry: Optional registry (uses instance registry if None)

        Returns:
            Total number of prompts imported

        Raises:
            ValueError: If no registry available
        """
        target_registry = registry or self._registry
        if not target_registry:
            msg = "No registry available for import"
            raise ValueError(msg)

        schemas = self.load_directory(dirpath)

        total_count = 0
        for schema in schemas:
            for prompt in schema.prompts:
                target_registry.register(prompt)
                total_count += 1

        self._logger.info(
            "directory_imported",
            path=str(dirpath),
            total_count=total_count,
        )

        return total_count

    @staticmethod
    def create_example_yaml(output_path: Path) -> None:
        """
        Create an example YAML file with proper schema.

        Args:
            output_path: Where to write the example file
        """
        example = {
            "version": "1.0.0",
            "metadata": {
                "description": "Example prompt schema",
                "author": "System",
            },
            "prompts": [
                {
                    "id": "greeting",
                    "version": "1.0.0",
                    "format": "text",
                    "status": "active",
                    "template": {
                        "content": "Hello {{name}}! Welcome to {{service}}.",
                        "variables": ["name", "service"],
                    },
                    "metadata": {
                        "author": "System",
                        "description": "Simple greeting prompt",
                        "tags": ["greeting", "welcome"],
                        "category": "user-interaction",
                    },
                },
                {
                    "id": "customer_support",
                    "version": "1.0.0",
                    "format": "chat",
                    "status": "active",
                    "chat_template": {
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful customer support agent for {{company}}.",
                            },
                            {
                                "role": "user",
                                "content": "{{customer_query}}",
                            },
                        ],
                        "variables": ["company", "customer_query"],
                    },
                    "metadata": {
                        "author": "Support Team",
                        "description": "Customer support chat template",
                        "tags": ["support", "chat"],
                        "category": "customer-service",
                        "model_recommendations": ["gpt-4", "claude-3"],
                        "temperature": 0.7,
                    },
                },
            ],
        }

        with output_path.open("w") as f:
            yaml.dump(example, f, default_flow_style=False, sort_keys=False)

        logger.info("example_yaml_created", path=str(output_path))
