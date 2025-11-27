"""
Version store for tracking prompt history and changes.

Implements VersionStoreProtocol with in-memory and file-based storage.
"""

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from prompt_manager.core.models import PromptVersion
from prompt_manager.exceptions import PromptNotFoundError, VersionError, VersionNotFoundError

logger = structlog.get_logger(__name__)


class VersionStore:
    """
    Version store with optional file-based persistence.

    Tracks version history, changelogs, and relationships between versions.
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        """
        Initialize version store.

        Args:
            storage_path: Optional path for file-based persistence
        """
        self._versions: dict[str, list[PromptVersion]] = defaultdict(list)
        self._storage_path = storage_path
        self._logger = logger.bind(component="version_store")

        if storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)

    def save_version(self, version: PromptVersion) -> None:
        """
        Save a prompt version.

        Usage:
            version_store.save_version(version)

        Args:
            version: Prompt version to save

        Raises:
            VersionError: If save fails
        """
        prompt_id = version.prompt.id

        self._logger.info(
            "saving_version",
            prompt_id=prompt_id,
            version=version.version,
        )

        # Calculate checksum
        version_with_checksum = self._add_checksum(version)

        # Add to memory store
        self._versions[prompt_id].append(version_with_checksum)

        # Sort by version
        self._versions[prompt_id].sort(
            key=lambda v: self._version_key(v.version),
            reverse=True,
        )

        # Persist to file if configured
        if self._storage_path:
            self._persist_version(version_with_checksum)

        self._logger.info(
            "version_saved",
            prompt_id=prompt_id,
            version=version.version,
        )

    def get_version(self, prompt_id: str, version: str) -> PromptVersion:
        """
        Get a specific version.

        Usage:
            version = version_store.get_version(prompt_id, version)

        Args:
            prompt_id: Prompt identifier
            version: Version string

        Returns:
            Prompt version

        Raises:
            VersionNotFoundError: If version doesn't exist
        """
        if prompt_id not in self._versions:
            raise VersionNotFoundError(prompt_id, version)

        for v in self._versions[prompt_id]:
            if v.version == version:
                return v

        raise VersionNotFoundError(prompt_id, version)

    def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        """
        List all versions for a prompt.

        Usage:
            versions = version_store.list_versions(prompt_id)

        Args:
            prompt_id: Prompt identifier

        Returns:
            List of versions, newest first

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        if prompt_id not in self._versions:
            raise PromptNotFoundError(prompt_id)

        return list(self._versions[prompt_id])

    def get_latest(self, prompt_id: str) -> PromptVersion:
        """
        Get the latest version.

        Usage:
            latest = version_store.get_latest(prompt_id)

        Args:
            prompt_id: Prompt identifier

        Returns:
            Latest version

        Raises:
            PromptNotFoundError: If no versions exist
        """
        if prompt_id not in self._versions or not self._versions[prompt_id]:
            raise PromptNotFoundError(prompt_id)

        return self._versions[prompt_id][0]  # Already sorted newest first

    def get_history(
        self,
        prompt_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[PromptVersion]:
        """
        Get version history with time filters.

        Usage:
            history = version_store.get_history(prompt_id, since=some_date)

        Args:
            prompt_id: Prompt identifier
            since: Only versions after this time
            until: Only versions before this time

        Returns:
            Filtered version history

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        if prompt_id not in self._versions:
            raise PromptNotFoundError(prompt_id)

        versions = self._versions[prompt_id]

        # Apply time filters
        if since or until:
            filtered = []
            for v in versions:
                if since and v.created_at < since:
                    continue
                if until and v.created_at > until:
                    continue
                filtered.append(v)
            return filtered

        return list(versions)

    def get_changelog(
        self,
        prompt_id: str,
        from_version: str | None = None,
        to_version: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get changelog entries between versions.

        Usage:
            changelog = version_store.get_changelog(prompt_id, from_version="1.0.0")

        Args:
            prompt_id: Prompt identifier
            from_version: Starting version (oldest in range)
            to_version: Ending version (newest in range)

        Returns:
            List of changelog entries

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        versions = self.list_versions(prompt_id)

        # Determine version range
        start_idx = 0
        end_idx = len(versions)

        if to_version:
            for i, v in enumerate(versions):
                if v.version == to_version:
                    end_idx = i + 1
                    break

        if from_version:
            for i, v in enumerate(versions):
                if v.version == from_version:
                    start_idx = i
                    break

        # Extract changelog entries
        changelog_entries = []
        for v in versions[start_idx:end_idx]:
            if v.changelog:
                changelog_entries.append(
                    {
                        "version": v.version,
                        "created_at": v.created_at.isoformat(),
                        "created_by": v.created_by,
                        "changelog": v.changelog,
                        "parent_version": v.parent_version,
                    }
                )

        return changelog_entries

    def compare_versions(
        self,
        prompt_id: str,
        version1: str,
        version2: str,
    ) -> dict[str, Any]:
        """
        Compare two versions and return differences.

        Usage:
            differences = version_store.compare_versions(prompt_id, "1.0.0", "1.1.0")

        Args:
            prompt_id: Prompt identifier
            version1: First version
            version2: Second version

        Returns:
            Dictionary of differences

        Raises:
            VersionNotFoundError: If either version doesn't exist
        """
        v1 = self.get_version(prompt_id, version1)
        v2 = self.get_version(prompt_id, version2)

        # Compare checksums
        checksums_differ = v1.checksum != v2.checksum

        # Compare key fields
        differences = {
            "versions": {"from": version1, "to": version2},
            "checksums_differ": checksums_differ,
            "status_changed": v1.prompt.status != v2.prompt.status,
            "template_changed": self._templates_differ(v1, v2),
            "metadata_changed": self._metadata_differ(v1, v2),
        }

        return differences

    def load_from_storage(self) -> int:
        """
        Load all versions from file storage.

        Usage:
            count = version_store.load_from_storage()

        Returns:
            Number of versions loaded

        Raises:
            VersionError: If loading fails
        """
        if not self._storage_path:
            return 0

        self._logger.info("loading_versions_from_storage")

        count = 0
        for version_file in self._storage_path.glob("*.json"):
            try:
                with open(version_file, "r") as f:
                    content = f.read()
                    data = json.loads(content)
                    version = PromptVersion.model_validate(data)

                    prompt_id = version.prompt.id
                    self._versions[prompt_id].append(version)
                    count += 1

            except Exception as e:
                self._logger.error(
                    "failed_to_load_version",
                    file=str(version_file),
                    error=str(e),
                )

        # Sort all versions
        for prompt_id in self._versions:
            self._versions[prompt_id].sort(
                key=lambda v: self._version_key(v.version),
                reverse=True,
            )

        self._logger.info("versions_loaded", count=count)
        return count

    def _add_checksum(self, version: PromptVersion) -> PromptVersion:
        """Add checksum to version if not present."""
        if version.checksum:
            return version

        # Calculate checksum from prompt content
        # Note: Pydantic v2 model_dump_json doesn't have sort_keys parameter
        # so we need to dump to dict first, then use json.dumps with sort_keys
        import json
        content_dict = version.prompt.model_dump(mode='json')
        content = json.dumps(content_dict, sort_keys=True)
        checksum = hashlib.sha256(content.encode()).hexdigest()

        # Create new version with checksum (PromptVersion is frozen)
        return PromptVersion(
            prompt=version.prompt,
            version=version.version,
            created_at=version.created_at,
            created_by=version.created_by,
            changelog=version.changelog,
            parent_version=version.parent_version,
            checksum=checksum,
        )

    def _persist_version(self, version: PromptVersion) -> None:
        """Persist version to file."""
        if not self._storage_path:
            return

        filename = f"{version.prompt.id}_{version.version}.json"
        filepath = self._storage_path / filename

        try:
            # Serialize to JSON
            data = version.model_dump(mode="json")

            with open(filepath, "w") as f:
                f.write(json.dumps(data, indent=2))

        except Exception as e:
            msg = f"Failed to persist version: {e}"
            raise VersionError(msg) from e

    @staticmethod
    def _version_key(version: str) -> tuple[int, int, int]:
        """Convert semantic version to sortable tuple."""
        parts = version.split(".")
        return int(parts[0]), int(parts[1]), int(parts[2])

    @staticmethod
    def _templates_differ(v1: PromptVersion, v2: PromptVersion) -> bool:
        """Check if templates differ between versions."""
        if v1.prompt.template and v2.prompt.template:
            return v1.prompt.template.content != v2.prompt.template.content
        if v1.prompt.chat_template and v2.prompt.chat_template:
            return v1.prompt.chat_template != v2.prompt.chat_template
        return False

    @staticmethod
    def _metadata_differ(v1: PromptVersion, v2: PromptVersion) -> bool:
        """Check if metadata differs between versions."""
        return v1.prompt.metadata != v2.prompt.metadata
