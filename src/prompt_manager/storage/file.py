"""File system storage backend with JSON persistence."""

import json
from pathlib import Path

import aiofiles
import structlog

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

    Stores prompts as JSON files in a directory structure:
    {base_path}/{prompt_id}/{version}.json
    """

    def __init__(self, base_path: Path) -> None:
        """
        Initialize file system storage.

        Args:
            base_path: Base directory for storage
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._logger = logger.bind(component="file_storage", path=str(base_path))

    async def save(self, prompt: Prompt) -> None:
        """
        Save a prompt to file system.

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

        prompt_dir = self._base_path / prompt.id
        prompt_dir.mkdir(parents=True, exist_ok=True)

        filepath = prompt_dir / f"{prompt.version}.json"

        try:
            # Serialize to JSON
            data = prompt.model_dump(mode="json")

            async with aiofiles.open(filepath, "w") as f:
                await f.write(json.dumps(data, indent=2))

            self._logger.info(
                "prompt_saved",
                prompt_id=prompt.id,
                version=prompt.version,
                path=str(filepath),
            )

        except Exception as e:
            msg = f"Failed to save prompt {prompt.id}: {e}"
            raise StorageWriteError(msg) from e

    async def load(self, prompt_id: str, version: str | None = None) -> Prompt:
        """
        Load a prompt from file system.

        Args:
            prompt_id: Prompt identifier
            version: Optional version (loads latest if None)

        Returns:
            Loaded prompt

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            StorageReadError: If read fails
        """
        prompt_dir = self._base_path / prompt_id

        if not prompt_dir.exists():
            raise PromptNotFoundError(prompt_id, version)

        try:
            if version:
                filepath = prompt_dir / f"{version}.json"
                if not filepath.exists():
                    raise PromptNotFoundError(prompt_id, version)
            else:
                # Find latest version
                version_files = list(prompt_dir.glob("*.json"))
                if not version_files:
                    raise PromptNotFoundError(prompt_id, version)

                # Get latest by semantic version
                versions = [f.stem for f in version_files]
                latest = max(versions, key=self._version_key)
                filepath = prompt_dir / f"{latest}.json"

            # Load and deserialize
            async with aiofiles.open(filepath, "r") as f:
                content = await f.read()
                data = json.loads(content)
                prompt = Prompt.model_validate(data)

            self._logger.debug(
                "prompt_loaded",
                prompt_id=prompt_id,
                version=prompt.version,
            )

            return prompt

        except PromptNotFoundError:
            raise
        except Exception as e:
            msg = f"Failed to load prompt {prompt_id}: {e}"
            raise StorageReadError(msg) from e

    async def delete(self, prompt_id: str, version: str | None = None) -> None:
        """
        Delete a prompt from file system.

        Args:
            prompt_id: Prompt identifier
            version: Optional version (deletes all if None)

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            StorageError: If delete fails
        """
        prompt_dir = self._base_path / prompt_id

        if not prompt_dir.exists():
            raise PromptNotFoundError(prompt_id, version)

        try:
            if version:
                filepath = prompt_dir / f"{version}.json"
                if not filepath.exists():
                    raise PromptNotFoundError(prompt_id, version)
                filepath.unlink()

                # Remove directory if empty
                if not any(prompt_dir.iterdir()):
                    prompt_dir.rmdir()
            else:
                # Delete entire directory
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
            StorageReadError: If listing fails
        """
        prompts = []

        try:
            # Iterate over prompt directories
            for prompt_dir in self._base_path.iterdir():
                if not prompt_dir.is_dir():
                    continue

                prompt_id = prompt_dir.name

                # Load latest version
                try:
                    prompt = await self.load(prompt_id)

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

    async def exists(self, prompt_id: str, version: str | None = None) -> bool:
        """
        Check if a prompt exists.

        Args:
            prompt_id: Prompt identifier
            version: Optional version

        Returns:
            True if exists
        """
        prompt_dir = self._base_path / prompt_id

        if not prompt_dir.exists():
            return False

        if version:
            filepath = prompt_dir / f"{version}.json"
            return filepath.exists()

        # Check if any version exists
        return any(prompt_dir.glob("*.json"))

    @staticmethod
    def _version_key(version: str) -> tuple[int, int, int]:
        """Convert semantic version to sortable tuple."""
        parts = version.split(".")
        return int(parts[0]), int(parts[1]), int(parts[2])
