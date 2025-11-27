"""
File system storage backend with YAML as single source of truth.

Storage Strategy:
- YAML files (prompts/{id}.yaml) are the single source of truth for current prompt versions
- YAML snapshots (prompts/{id}/_versions/{version}.yaml) are created for version history
- YAML format is preferred because it uses fewer tokens for LLMs to process
- All reads prefer YAML; supports legacy JSON snapshots for backward compatibility
"""

import json
from pathlib import Path

import structlog
import yaml

from prompt_manager.core.models import Prompt
from prompt_manager.exceptions import (
    PromptNotFoundError,
    StorageError,
    StorageReadError,
    StorageWriteError,
)

logger = structlog.get_logger(__name__)


class FileSystemStorage:
    """
    File system storage backend implementing StorageBackendProtocol.

    Storage structure:
    - Current version: {base_path}/{prompt_id}.yaml (YAML - single source of truth)
    - Version history: {base_path}/{prompt_id}/_versions/{version}.yaml (YAML snapshots)

    Why YAML everywhere?
    - Fewer tokens for LLMs to process
    - More human-readable for editing
    - Cleaner diffs in version control
    - Consistent format across all storage
    """

    def __init__(self, base_path: Path, save_version_snapshots: bool = True) -> None:
        """
        Initialize file system storage.

        Args:
            base_path: Base directory for storage
            save_version_snapshots: Whether to save YAML version snapshots (default: True)
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._save_version_snapshots = save_version_snapshots
        self._logger = logger.bind(component="file_storage", path=str(base_path))

    def save(self, prompt: Prompt) -> None:
        """
        Save a prompt to file system as YAML (current version and version snapshot).

        Creates:
        1. YAML file as single source of truth: {base_path}/{prompt_id}.yaml
        2. Optional YAML snapshot for version history: {base_path}/{prompt_id}/_versions/{version}.yaml

        Args:
            prompt: Prompt to save

        Raises:
            StorageWriteError: If save fails
        """
        self._logger.debug(
            "saving_prompt",
            prompt_id=prompt.id,
            version=prompt.version,
        )

        try:
            # 1. Save current version as YAML (single source of truth)
            yaml_filepath = self._base_path / f"{prompt.id}.yaml"
            data = prompt.model_dump(mode="json")

            # Write YAML with clean formatting
            with open(yaml_filepath, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=2,
                )

            self._logger.info(
                "prompt_saved_yaml",
                prompt_id=prompt.id,
                version=prompt.version,
                path=str(yaml_filepath),
            )

            # 2. Optionally save version snapshot as YAML for history
            if self._save_version_snapshots:
                version_dir = self._base_path / prompt.id / "_versions"
                version_dir.mkdir(parents=True, exist_ok=True)

                version_filepath = version_dir / f"{prompt.version}.yaml"

                # Write YAML version snapshot with clean formatting
                with open(version_filepath, "w", encoding="utf-8") as f:
                    yaml.dump(
                        data,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                        indent=2,
                    )

                self._logger.debug(
                    "version_snapshot_saved",
                    prompt_id=prompt.id,
                    version=prompt.version,
                    path=str(version_filepath),
                )

        except Exception as e:
            msg = f"Failed to save prompt {prompt.id}: {e}"
            raise StorageWriteError(msg) from e

    def load(self, prompt_id: str, version: str | None = None) -> Prompt:
        """
        Load a prompt from file system.

        Loading strategy:
        - If no version specified: Load from YAML file (current version)
        - If version specified: Load from YAML snapshot in _versions/ folder
        - Falls back to legacy JSON format if YAML not found

        Args:
            prompt_id: Prompt identifier
            version: Optional version (loads latest from YAML if None)

        Returns:
            Loaded prompt

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            StorageReadError: If read fails
        """
        try:
            if version:
                # Try to load specific version from YAML snapshot (preferred)
                yaml_version_file = self._base_path / prompt_id / "_versions" / f"{version}.yaml"
                json_version_file = self._base_path / prompt_id / "_versions" / f"{version}.json"

                if yaml_version_file.exists():
                    with open(yaml_version_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        prompt = Prompt.model_validate(data)

                    self._logger.debug(
                        "prompt_loaded_from_yaml_snapshot",
                        prompt_id=prompt_id,
                        version=version,
                    )
                    return prompt

                elif json_version_file.exists():
                    # Legacy JSON support for backward compatibility
                    with open(json_version_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        prompt = Prompt.model_validate(data)

                    self._logger.debug(
                        "prompt_loaded_from_json_snapshot",
                        prompt_id=prompt_id,
                        version=version,
                    )
                    return prompt

                else:
                    raise PromptNotFoundError(prompt_id, version)

            else:
                # Load current version from YAML file
                yaml_file = self._base_path / f"{prompt_id}.yaml"

                if not yaml_file.exists():
                    raise PromptNotFoundError(prompt_id, version)

                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    prompt = Prompt.model_validate(data)

                self._logger.debug(
                    "prompt_loaded_from_yaml",
                    prompt_id=prompt_id,
                    version=prompt.version,
                )

                return prompt

        except PromptNotFoundError:
            raise
        except Exception as e:
            msg = f"Failed to load prompt {prompt_id}: {e}"
            raise StorageReadError(msg) from e

    def delete(self, prompt_id: str, version: str | None = None) -> None:
        """
        Delete a prompt from file system.

        Deletion strategy:
        - If version specified: Delete both YAML and JSON snapshots (if they exist)
        - If no version: Delete YAML file and entire version history folder

        Args:
            prompt_id: Prompt identifier
            version: Optional version (deletes all if None)

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            StorageError: If delete fails
        """
        try:
            if version:
                # Delete specific version snapshot (both YAML and JSON if present)
                yaml_version_file = self._base_path / prompt_id / "_versions" / f"{version}.yaml"
                json_version_file = self._base_path / prompt_id / "_versions" / f"{version}.json"

                found = False
                if yaml_version_file.exists():
                    yaml_version_file.unlink()
                    found = True

                if json_version_file.exists():
                    json_version_file.unlink()
                    found = True

                if not found:
                    raise PromptNotFoundError(prompt_id, version)

                # Remove version directory if empty
                version_dir = self._base_path / prompt_id / "_versions"
                if version_dir.exists() and not any(version_dir.iterdir()):
                    version_dir.rmdir()

                # Remove prompt directory if empty
                prompt_dir = self._base_path / prompt_id
                if prompt_dir.exists() and not any(prompt_dir.iterdir()):
                    prompt_dir.rmdir()

            else:
                # Delete YAML file and entire version history
                yaml_file = self._base_path / f"{prompt_id}.yaml"

                if not yaml_file.exists():
                    raise PromptNotFoundError(prompt_id, version)

                yaml_file.unlink()

                # Delete version history folder if it exists
                prompt_dir = self._base_path / prompt_id
                if prompt_dir.exists():
                    import shutil
                    shutil.rmtree(prompt_dir)

            self._logger.info(
                "prompt_deleted",
                prompt_id=prompt_id,
                version=version,
            )

        except PromptNotFoundError:
            raise
        except Exception as e:
            msg = f"Failed to delete prompt {prompt_id}: {e}"
            raise StorageError(msg) from e

    def list(
        self,
        *,
        tags: list[str] | None = None,
        status: str | None = None,
    ) -> list[Prompt]:
        """
        List prompts matching filters.

        Loads only from YAML files (current versions), ignoring old JSON files.

        Args:
            tags: Filter by tags
            status: Filter by status

        Returns:
            List of matching prompts

        Raises:
            StorageReadError: If listing fails
        """
        prompts = []

        try:
            # Iterate over YAML files only (current versions)
            for yaml_file in self._base_path.glob("*.yaml"):
                if not yaml_file.is_file():
                    continue

                prompt_id = yaml_file.stem

                # Load current version
                try:
                    prompt = self.load(prompt_id)

                    # Apply filters
                    if status and prompt.status.value != status:
                        continue

                    if tags:
                        prompt_tags = set(prompt.metadata.tags)
                        if not all(tag in prompt_tags for tag in tags):
                            continue

                    prompts.append(prompt)

                except Exception as e:
                    self._logger.warning(
                        "failed_to_load_prompt",
                        prompt_id=prompt_id,
                        error=str(e),
                    )
                    continue

            return prompts

        except Exception as e:
            msg = f"Failed to list prompts: {e}"
            raise StorageReadError(msg) from e

    def exists(self, prompt_id: str, version: str | None = None) -> bool:
        """
        Check if a prompt exists.

        Args:
            prompt_id: Prompt identifier
            version: Optional version

        Returns:
            True if exists
        """
        if version:
            # Check for specific version snapshot (YAML or JSON)
            yaml_version_file = self._base_path / prompt_id / "_versions" / f"{version}.yaml"
            json_version_file = self._base_path / prompt_id / "_versions" / f"{version}.json"
            return yaml_version_file.exists() or json_version_file.exists()
        else:
            # Check for current YAML file
            yaml_file = self._base_path / f"{prompt_id}.yaml"
            return yaml_file.exists()

    @staticmethod
    def _version_key(version: str) -> tuple[int, int, int]:
        """Convert semantic version to sortable tuple."""
        parts = version.split(".")
        return int(parts[0]), int(parts[1]), int(parts[2])
