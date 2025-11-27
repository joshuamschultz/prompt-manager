"""In-memory storage backend for testing and development."""

from __future__ import annotations

from collections import defaultdict

import structlog

from prompt_manager.core.models import Prompt, PromptStatus
from prompt_manager.exceptions import PromptNotFoundError

logger = structlog.get_logger(__name__)


class InMemoryStorage:
    """
    In-memory storage backend implementing StorageBackendProtocol.

    Useful for testing and development. Does not persist data.
    """

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._storage: dict[str, dict[str, Prompt]] = defaultdict(dict)
        self._logger = logger.bind(component="memory_storage")

    def save(self, prompt: Prompt) -> None:
        """
        Save a prompt to memory.

        Args:
            prompt: Prompt to save
        """
        self._logger.debug(
            "saving_prompt",
            prompt_id=prompt.id,
            version=prompt.version,
        )

        self._storage[prompt.id][prompt.version] = prompt

    def load(self, prompt_id: str, version: str | None = None) -> Prompt:
        """
        Load a prompt from memory.

        Args:
            prompt_id: Prompt identifier
            version: Optional version (loads latest if None)

        Returns:
            Loaded prompt

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        if prompt_id not in self._storage:
            raise PromptNotFoundError(prompt_id, version)

        versions = self._storage[prompt_id]
        if not versions:
            raise PromptNotFoundError(prompt_id, version)

        if version:
            if version not in versions:
                raise PromptNotFoundError(prompt_id, version)
            return versions[version]

        # Get latest version
        latest_version = max(versions.keys(), key=self._version_key)
        return versions[latest_version]

    def delete(self, prompt_id: str, version: str | None = None) -> None:
        """
        Delete a prompt from memory.

        Args:
            prompt_id: Prompt identifier
            version: Optional version (deletes all if None)

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        if prompt_id not in self._storage:
            raise PromptNotFoundError(prompt_id, version)

        if version:
            if version not in self._storage[prompt_id]:
                raise PromptNotFoundError(prompt_id, version)
            del self._storage[prompt_id][version]
        else:
            del self._storage[prompt_id]

    def list(
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
        """
        prompts = []

        for prompt_id, versions in self._storage.items():
            if not versions:
                continue

            # Get latest version
            latest_version = max(versions.keys(), key=self._version_key)
            prompt = versions[latest_version]

            # Apply filters
            if status and prompt.status.value != status:
                continue

            if tags:
                prompt_tags = set(prompt.metadata.tags)
                if not all(tag in prompt_tags for tag in tags):
                    continue

            prompts.append(prompt)

        return prompts

    def exists(self, prompt_id: str, version: str | None = None) -> bool:
        """
        Check if a prompt exists.

        Args:
            prompt_id: Prompt identifier
            version: Optional version

        Returns:
            True if exists
        """
        if prompt_id not in self._storage:
            return False

        if version:
            return version in self._storage[prompt_id]

        return bool(self._storage[prompt_id])

    def clear(self) -> None:
        """Clear all prompts from storage."""
        self._logger.warning("clearing_storage")
        self._storage.clear()

    @staticmethod
    def _version_key(version: str) -> tuple[int, int, int]:
        """Convert semantic version to sortable tuple."""
        parts = version.split(".")
        return int(parts[0]), int(parts[1]), int(parts[2])
