"""
Prompt Manager - Modern Python 3.11+ prompt management system.

A production-ready prompt management system with:
- Pydantic v2 validation
- YAML schema support
- Handlebars templating
- Plugin architecture for multiple LLM frameworks
- Observability and telemetry hooks
- Versioning and history tracking
- Async/await support
"""

from prompt_manager.core.manager import PromptManager
from prompt_manager.core.models import Prompt, PromptMetadata, PromptVersion
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.core.template import TemplateEngine
from prompt_manager.exceptions import (
    PromptError,
    PromptManagerError,
    PromptNotFoundError,
    PromptValidationError,
    TemplateError,
)
from prompt_manager.versioning.store import VersionStore

__version__ = "0.1.0"

__all__ = [
    # Main API
    "PromptManager",
    # Core models
    "Prompt",
    "PromptMetadata",
    "PromptVersion",
    # Registry and storage
    "PromptRegistry",
    "VersionStore",
    # Templating
    "TemplateEngine",
    # Exceptions
    "PromptError",
    "PromptManagerError",
    "PromptNotFoundError",
    "PromptValidationError",
    "TemplateError",
    # Version
    "__version__",
]
