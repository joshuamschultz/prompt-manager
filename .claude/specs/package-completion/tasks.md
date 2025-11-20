# Implementation Plan: Package Completion for Production Release

## What We're NOT Doing
**CRITICAL**: These items are explicitly out of scope for this implementation.

- NOT implementing LLM API calls directly - package manages prompts, frameworks handle API calls
- NOT building a web dashboard or admin UI - CLI and programmatic API only
- NOT migrating existing prompt formats from other systems - users define prompts in our format
- NOT implementing database storage backends (PostgreSQL, Redis) - filesystem and in-memory only for v1.0
- NOT building REST API server - Python package/library only
- NOT implementing A/B testing or analytics - basic metrics collection only
- NOT creating hosted/cloud version - self-hosted library only
- NOT supporting Python versions below 3.11 - modern Python only
- NOT implementing custom LLM client wrappers - use existing framework clients

**Why This Matters**: Focus only on tasks listed below. If unsure whether something is in scope, check requirements.md. This feature focuses on packaging, distribution, and integration patterns. Advanced features are intentionally deferred.

---

## Phase 1: Core Integration Framework

### Setup and Foundation
- [ ] 1. Create integration module structure
  - Create directory `src/prompt_manager/integrations/`
  - Create `__init__.py` with lazy import pattern using `__getattr__`
  - Create `__all__` list with public API exports
  - Add docstring explaining integration purpose
  - _Requirements: 1.1, 2.5_

- [ ] 2. Add type marker file for PEP 561
  - Create empty `src/prompt_manager/py.typed` file
  - Verify file is included in package manifest
  - Test that mypy recognizes distributed type hints
  - _Requirements: 1.1, 5.3_

### Exception Handling
- [ ] 3. Implement integration exception classes
  - Open `src/prompt_manager/exceptions.py`
  - Add `IntegrationError(PromptManagerError)` base class
  - Add `IntegrationNotAvailableError(IntegrationError)` with integration name and extra parameter
  - Add `ConversionError(IntegrationError)` for conversion failures
  - Add `IncompatibleFormatError(IntegrationError)` for format mismatches
  - Include clear error messages with install commands
  - _Requirements: 2.5, 3.2_

- [ ] 4. Write unit tests for exception classes
  - Test `IntegrationNotAvailableError` message formatting
  - Test exception hierarchy and inheritance
  - Test exception serialization for logging
  - Verify error messages include install commands
  - _Requirements: 2.5_

### Base Integration Class
- [ ] 5. Implement BaseIntegration abstract class
  - Create `src/prompt_manager/integrations/base.py`
  - Define `BaseIntegration(ABC, Generic[T])` class
  - Add `__init__` with `template_engine` and `strict_validation` parameters
  - Add abstract `async def convert(prompt, variables) -> T` method
  - Add abstract `def validate_compatibility(prompt) -> bool` method
  - Include comprehensive docstrings with parameter types
  - _Requirements: 2.5_

- [ ] 6. Write unit tests for BaseIntegration
  - Test instantiation with template engine
  - Test that abstract methods raise NotImplementedError
  - Test strict_validation parameter handling
  - Create mock concrete implementation for testing
  - _Requirements: 2.5_

### Type Definitions
- [ ] 7. Create integration type aliases
  - Create `src/prompt_manager/integrations/types.py`
  - Define `OpenAIMessage: TypeAlias = dict[str, Any]`
  - Define `OpenAIChatCompletion: TypeAlias = list[OpenAIMessage]`
  - Define `AnthropicMessage: TypeAlias = dict[str, Any]`
  - Define `AnthropicRequest: TypeAlias = dict[str, Any]`
  - Define `LangChainPrompt: TypeAlias = Any`
  - Include docstrings explaining each type
  - _Requirements: 5.3_

- [ ] 8. Create TypedDict classes for message formats
  - Create `OpenAIMessage(TypedDict)` with role, content, name, function_call, tool_calls
  - Create `AnthropicMessage(TypedDict)` with role and content
  - Mark optional fields with `total=False`
  - Add type annotations for all fields
  - _Requirements: 2.1, 2.2, 5.3_

- [ ] 9. Write type checking validation tests
  - Test TypedDict structure matches expected format
  - Verify mypy accepts valid message dictionaries
  - Verify mypy rejects invalid message dictionaries
  - Test with mypy strict mode enabled
  - _Requirements: 5.3_

---

## Phase 2: Framework Integrations

### OpenAI Integration
- [ ] 10. Implement OpenAI integration class
  - Create `src/prompt_manager/integrations/openai.py`
  - Implement `OpenAIIntegration(BaseIntegration[list[OpenAIMessage] | str])`
  - Implement `async def convert()` method dispatching to _convert_chat or _convert_text
  - Implement `async def _convert_chat()` method for CHAT format
  - Implement `async def _convert_text()` method for TEXT format
  - Implement `def _map_role()` method for role mapping (SYSTEM→system, USER→user, etc.)
  - Implement `def validate_compatibility()` returning True (supports all formats)
  - _Requirements: 2.1_

- [ ] 11. Write unit tests for OpenAI integration
  - Test text prompt conversion to string
  - Test chat prompt conversion to message list
  - Test role mapping for all Role enum values
  - Test missing template raises IntegrationError
  - Test variable substitution in templates
  - Test function_call and tool_calls preservation
  - Test message name field handling
  - _Requirements: 2.1, 5.1_

- [ ] 12. Create OpenAI integration plugin
  - Create `src/prompt_manager/plugins/openai_plugin.py`
  - Implement `OpenAIPlugin(BasePlugin)` class
  - Implement `async def _initialize_impl()` to create OpenAIIntegration
  - Implement `async def render_for_framework()` delegating to integration
  - Implement `async def validate_compatibility()` delegating to integration
  - Add plugin name "openai" and version "1.0.0"
  - _Requirements: 2.1, 2.5, 7.1_

- [ ] 13. Write unit tests for OpenAI plugin
  - Test plugin initialization
  - Test render_for_framework returns correct format
  - Test validate_compatibility logic
  - Test plugin discovery via entry point
  - Test error handling when integration fails
  - _Requirements: 2.1, 5.1, 7.1_

### Anthropic Integration
- [ ] 14. Implement Anthropic integration class
  - Create `src/prompt_manager/integrations/anthropic.py`
  - Implement `AnthropicIntegration(BaseIntegration[dict[str, Any]])`
  - Implement `async def convert()` extracting system message and building messages array
  - Implement `def _map_role()` mapping USER/FUNCTION/TOOL→user, ASSISTANT→assistant
  - Implement `def _validate_alternation()` checking message role alternation
  - Raise error if multiple system messages found
  - Raise error if first message not from user
  - Implement `def validate_compatibility()` checking for CHAT format
  - _Requirements: 2.2_

- [ ] 15. Write unit tests for Anthropic integration
  - Test chat prompt conversion to {system, messages} format
  - Test single system message extraction
  - Test error on multiple system messages
  - Test error on first message not being user
  - Test message alternation validation
  - Test role mapping for supported roles
  - Test error on unsupported format (TEXT)
  - Test error on unsupported role
  - _Requirements: 2.2, 5.1_

- [ ] 16. Create Anthropic integration plugin
  - Create `src/prompt_manager/plugins/anthropic_plugin.py`
  - Implement `AnthropicPlugin(BasePlugin)` class
  - Implement `async def _initialize_impl()` to create AnthropicIntegration
  - Implement `async def render_for_framework()` delegating to integration
  - Implement `async def validate_compatibility()` delegating to integration
  - Add plugin name "anthropic" and version "1.0.0"
  - _Requirements: 2.2, 2.5, 7.1_

- [ ] 17. Write unit tests for Anthropic plugin
  - Test plugin initialization
  - Test render_for_framework returns Anthropic format
  - Test validate_compatibility rejects TEXT format
  - Test plugin discovery via entry point
  - Test error handling for conversion failures
  - _Requirements: 2.2, 5.1, 7.1_

### LangChain Integration
- [ ] 18. Implement LangChain integration class
  - Create `src/prompt_manager/integrations/langchain.py`
  - Add conditional import with try/except for langchain_core
  - Set `LANGCHAIN_AVAILABLE = True/False` based on import
  - Implement `LangChainIntegration(BaseIntegration[Any])`
  - Check LANGCHAIN_AVAILABLE in __init__, raise IntegrationNotAvailableError if False
  - Implement `async def convert()` dispatching by format
  - Implement `async def _convert_chat()` creating ChatPromptTemplate
  - Implement `async def _convert_text()` creating PromptTemplate
  - Implement `def _handlebars_to_fstring()` converting {{var}} to {var}
  - Implement `def validate_compatibility()` checking TEXT or CHAT format
  - _Requirements: 2.3_

- [ ] 19. Write unit tests for LangChain integration
  - Test dependency check raises error when langchain not installed
  - Test text prompt conversion to PromptTemplate
  - Test chat prompt conversion to ChatPromptTemplate
  - Test Handlebars to f-string conversion
  - Test system message becomes SystemMessagePromptTemplate
  - Test user message becomes HumanMessagePromptTemplate
  - Test partial variables preservation
  - Test compatibility validation for supported formats
  - _Requirements: 2.3, 5.1_

- [ ] 20. Create LangChain integration plugin
  - Create `src/prompt_manager/plugins/langchain_plugin.py`
  - Implement `LangChainPlugin(BasePlugin)` class
  - Implement `async def _initialize_impl()` to create LangChainIntegration
  - Implement `async def render_for_framework()` delegating to integration
  - Implement `async def validate_compatibility()` delegating to integration
  - Add plugin name "langchain" and version "1.0.0"
  - _Requirements: 2.3, 2.5, 7.1_

- [ ] 21. Write unit tests for LangChain plugin
  - Test plugin initialization
  - Test render_for_framework returns LangChain template
  - Test validate_compatibility logic
  - Test plugin discovery via entry point
  - Test error handling when langchain not installed
  - _Requirements: 2.3, 5.1, 7.1_

### LiteLLM Integration
- [ ] 22. Implement LiteLLM integration class
  - Create `src/prompt_manager/integrations/litellm.py`
  - Implement `LiteLLMIntegration(BaseIntegration[list[dict[str, Any]] | str])`
  - Create `OpenAIIntegration` instance in __init__ for delegation
  - Implement `async def convert()` delegating to OpenAI integration
  - Implement `def validate_compatibility()` returning True
  - Add docstring explaining LiteLLM uses OpenAI-compatible format
  - _Requirements: 2.4_

- [ ] 23. Write unit tests for LiteLLM integration
  - Test delegation to OpenAI integration
  - Test text prompt conversion
  - Test chat prompt conversion
  - Test compatibility validation
  - Test that output format matches OpenAI format
  - _Requirements: 2.4, 5.1_

- [ ] 24. Create LiteLLM integration plugin
  - Create `src/prompt_manager/plugins/litellm_plugin.py`
  - Implement `LiteLLMPlugin(BasePlugin)` class
  - Implement `async def _initialize_impl()` to create LiteLLMIntegration
  - Implement `async def render_for_framework()` delegating to integration
  - Implement `async def validate_compatibility()` delegating to integration
  - Add plugin name "litellm" and version "1.0.0"
  - _Requirements: 2.4, 2.5, 7.1_

- [ ] 25. Write unit tests for LiteLLM plugin
  - Test plugin initialization
  - Test render_for_framework returns correct format
  - Test validate_compatibility logic
  - Test plugin discovery via entry point
  - _Requirements: 2.4, 5.1, 7.1_

### Integration Module Exports
- [ ] 26. Implement lazy import pattern in integrations __init__
  - Open `src/prompt_manager/integrations/__init__.py`
  - Implement `__getattr__` function for lazy imports
  - Map "OpenAIIntegration" to openai module import
  - Map "AnthropicIntegration" to anthropic module import
  - Map "LangChainIntegration" to langchain module import
  - Map "LiteLLMIntegration" to litellm module import
  - Raise AttributeError for unknown names
  - Add BaseIntegration to `__all__`
  - _Requirements: 2.5_

- [ ] 27. Write tests for lazy import pattern
  - Test importing BaseIntegration (always available)
  - Test lazy import of OpenAIIntegration
  - Test lazy import of AnthropicIntegration
  - Test lazy import of LangChainIntegration
  - Test lazy import of LiteLLMIntegration
  - Test AttributeError on invalid import
  - Test import performance (should be fast)
  - _Requirements: 2.5_

---

## Phase 3: Documentation

### Core Documentation
- [x] 28. Create LICENSE file
  - Create `LICENSE` file in project root
  - Add MIT license text with current year
  - Add copyright holder name
  - Verify file included in package distribution
  - _Requirements: 1.2_

- [x] 29. Create SECURITY.md
  - Create `SECURITY.md` in project root
  - Add supported versions table
  - Add vulnerability reporting instructions (email or private issue)
  - Add security best practices (API keys, environment variables)
  - Document dependency scanning process
  - Add security response timeline (48 hours)
  - _Requirements: 1.2, 4.4_

- [x] 30. Create CONTRIBUTING.md
  - Create `CONTRIBUTING.md` in project root
  - Add development setup instructions
  - Document how to run tests (make test, make test-unit, make test-integration)
  - Document code quality commands (make lint, make format, make type-check)
  - Add section on creating integrations linking to INTEGRATION_GUIDE.md
  - Add pull request submission guidelines
  - Document pre-commit hook setup
  - _Requirements: 3.3, 4.1_

- [x] 31. Create RELEASING.md
  - Create `RELEASING.md` in project root
  - Add pre-release checklist (tests, coverage, type checking, security)
  - Document version bumping process (update __version__ and pyproject.toml)
  - Add TestPyPI testing steps
  - Add PyPI publishing steps
  - Add GitHub release creation steps
  - Document post-release verification
  - Add rollback procedures
  - _Requirements: 6.2, 6.3_

- [x] 32. Create docs/INTEGRATION_GUIDE.md
  - Create `docs/` directory if not exists
  - Create `docs/INTEGRATION_GUIDE.md`
  - Document BaseIntegration implementation steps
  - Add example custom integration code
  - Document plugin creation for auto-discovery
  - Add entry point registration instructions
  - Link to existing integration code as examples
  - Document testing best practices for integrations
  - _Requirements: 2.5, 4.3, 7.2_

### README Updates
- [x] 33. Update README.md with installation options
  - Open `README.md`
  - Update Installation section with all install methods
  - Add core package install: `pip install prompt-manager`
  - Add framework-specific extras: `[openai]`, `[anthropic]`, `[langchain]`, `[litellm]`
  - Add all extras install: `[all]`
  - Add development install: `poetry install --with dev -E all`
  - _Requirements: 3.1, 3.2, 4.1_

- [x] 34. Add Framework Integrations section to README
  - Add new section after Features
  - List all supported integrations (OpenAI, Anthropic, LangChain, LiteLLM)
  - Add brief description of each integration
  - Include benefits of using integrations
  - Link to examples directory
  - _Requirements: 4.1, 4.3_

- [x] 35. Add integration examples to README
  - Add "Framework Integration Examples" section
  - Add complete OpenAI SDK example with code snippet
  - Add complete Anthropic SDK example with code snippet
  - Add complete LangChain example with code snippet
  - Add complete LiteLLM example with code snippet
  - Include import statements and setup code
  - Link to `examples/integrations/` for full examples
  - _Requirements: 4.1, 4.3_

- [x] 36. Add PyPI badges to README
  - Add PyPI version badge
  - Add PyPI Python version badge
  - Add license badge
  - Add build status badge (placeholder for CI)
  - Add coverage badge (placeholder for CI)
  - Place badges at top of README
  - _Requirements: 4.1_

### Example Code
- [x] 37. Create examples directory structure
  - Create `examples/integrations/` directory
  - Create `examples/integrations/README.md` with overview
  - Create `examples/integrations/requirements.txt` listing optional dependencies
  - Add note about setting up API keys in environment
  - _Requirements: 4.3_

- [x] 38. Create OpenAI integration example
  - Create `examples/integrations/openai_example.py`
  - Import prompt_manager and OpenAIIntegration
  - Create sample prompt in code or load from file
  - Convert prompt to OpenAI format
  - Add mock API call example (commented out real call)
  - Include expected output in docstring
  - Add setup instructions and API key handling
  - _Requirements: 4.3_

- [x] 39. Create Anthropic integration example
  - Create `examples/integrations/anthropic_example.py`
  - Import prompt_manager and AnthropicIntegration
  - Create sample CHAT prompt with system message
  - Convert prompt to Anthropic format
  - Add mock API call example (commented out real call)
  - Include expected output in docstring
  - Add setup instructions and API key handling
  - _Requirements: 4.3_

- [x] 40. Create LangChain integration example
  - Create `examples/integrations/langchain_example.py`
  - Import prompt_manager and LangChainIntegration
  - Create sample prompt and convert to LangChain template
  - Show usage in LCEL chain composition
  - Add example with ChatPromptTemplate
  - Include expected output in docstring
  - Add setup instructions
  - _Requirements: 4.3_

- [x] 41. Create LiteLLM integration example
  - Create `examples/integrations/litellm_example.py`
  - Import prompt_manager and LiteLLMIntegration
  - Create sample prompt and convert to LiteLLM format
  - Show multi-provider routing example
  - Add mock API call example
  - Include expected output in docstring
  - Add setup instructions
  - _Requirements: 4.3_

- [x] 42. Create custom integration example
  - Create `examples/integrations/custom_integration_example.py`
  - Implement example custom integration extending BaseIntegration
  - Show conversion logic for hypothetical framework
  - Document all required methods
  - Add comments explaining each step
  - Include complete working code
  - _Requirements: 2.5, 4.3_

### API Documentation
- [ ] 43. Add docstrings to all integration classes
  - Verify all public classes have docstrings following Google style
  - Add parameter descriptions with types
  - Add return type descriptions
  - Add raises section for exceptions
  - Include usage examples in docstrings
  - Run docstring linter to verify format
  - _Requirements: 4.2_

- [ ] 44. Generate API reference documentation
  - Create `docs/api/` directory
  - Generate API reference from docstrings (using Sphinx or mkdocs)
  - Document BaseIntegration protocol
  - Document all framework integrations
  - Document exception classes
  - Include type aliases and TypedDict definitions
  - _Requirements: 4.2_

---

## Phase 4: Testing

### Unit Tests
- [x] 45. Write comprehensive unit tests for all integrations
  - Verify all integration tests in `tests/integrations/unit/` exist
  - Ensure tests cover all public methods
  - Test error conditions and edge cases
  - Test with invalid inputs
  - Test with missing required fields
  - Run tests and verify all pass
  - _Requirements: 5.1_

- [x] 46. Write tests for exception handling
  - Test IntegrationNotAvailableError message format
  - Test ConversionError context preservation
  - Test IncompatibleFormatError with different formats
  - Test exception inheritance chain
  - Test exception serialization for logging
  - _Requirements: 5.1_

- [x] 47. Write tests for type definitions
  - Test TypedDict accepts valid dictionaries
  - Test TypedDict rejects invalid dictionaries
  - Run mypy on test files to verify type checking
  - Test optional vs required fields
  - _Requirements: 5.3_

### Integration Tests
- [x] 48. Write OpenAI integration end-to-end test
  - Create `tests/integrations/integration/test_openai_integration_e2e.py`
  - Test full workflow: PromptManager → OpenAIIntegration → OpenAI SDK format
  - Mock OpenAI API responses
  - Test with real OpenAI SDK message validation
  - Test both CHAT and TEXT formats
  - Test variable substitution
  - Test function calling format
  - _Requirements: 5.1_

- [x] 49. Write Anthropic integration end-to-end test
  - Create `tests/integrations/integration/test_anthropic_integration_e2e.py`
  - Test full workflow: PromptManager → AnthropicIntegration → Anthropic format
  - Mock Anthropic API responses
  - Test system message extraction
  - Test message alternation validation
  - Test with Anthropic SDK if available
  - _Requirements: 5.1_

- [x] 50. Write LangChain integration end-to-end test
  - Create `tests/integrations/integration/test_langchain_integration_e2e.py`
  - Test full workflow: PromptManager → LangChainIntegration → LangChain templates
  - Test PromptTemplate creation and rendering
  - Test ChatPromptTemplate creation and rendering
  - Test LCEL chain composition
  - Test with real LangChain template validation
  - _Requirements: 5.1_

- [x] 51. Write LiteLLM integration end-to-end test
  - Create `tests/integrations/integration/test_litellm_integration_e2e.py`
  - Test full workflow: PromptManager → LiteLLMIntegration → LiteLLM format
  - Test multi-provider format compatibility
  - Mock LiteLLM API responses
  - Test model routing metadata
  - _Requirements: 5.1_

- [x] 52. Write plugin discovery integration test
  - Create `tests/integrations/integration/test_plugin_discovery.py`
  - Test entry point scanning
  - Test plugin auto-registration
  - Test plugin initialization
  - Test graceful failure when plugin dependencies missing
  - Test warning logs for failed plugin loads
  - _Requirements: 7.1, 5.1_

### Example Validation Tests
- [x] 53. Write example validation tests
  - Create `tests/integrations/examples/test_examples_run.py`
  - Test all example files can be imported without errors
  - Test example syntax is valid Python
  - Use importlib to dynamically load examples
  - Test with mocked API calls
  - Verify examples run without requiring API keys
  - _Requirements: 5.2_

- [x] 54. Write doctest for inline examples
  - Add doctest runner to test suite
  - Verify all docstring examples execute correctly
  - Add `# doctest: +SKIP` for examples requiring external dependencies
  - Run doctest in CI
  - _Requirements: 5.2_

### Type Checking Tests
- [x] 55. Configure mypy strict mode for integrations
  - Update `pyproject.toml` with mypy strict configuration
  - Enable strict mode for `src/prompt_manager/integrations/`
  - Add type checking to CI pipeline
  - Fix any type errors that arise
  - _Requirements: 5.3_

- [x] 56. Verify py.typed marker is effective
  - Install package in fresh environment
  - Run mypy on user code importing the package
  - Verify type hints are recognized
  - Test IDE autocomplete shows type information
  - _Requirements: 5.3_

### Test Coverage
- [x] 57. Run coverage analysis for integrations
  - Run pytest with coverage for `src/prompt_manager/integrations/`
  - Generate coverage report with line and branch coverage
  - Identify any uncovered code paths
  - Target 90%+ line coverage, 85%+ branch coverage
  - _Requirements: 5.1_

- [x] 58. Add missing tests to reach coverage targets
  - Review coverage report for gaps
  - Add tests for uncovered branches
  - Add tests for error paths
  - Add tests for edge cases
  - Re-run coverage to verify targets met
  - _Requirements: 5.1_

---

## Phase 5: CI/CD and Distribution

### Package Configuration
- [x] 59. Update pyproject.toml with framework dependencies
  - Open `pyproject.toml`
  - Add optional dependencies: openai ^1.57.0, anthropic ^0.42.0, langchain-core ^0.3.0, litellm ^1.53.0
  - Define extras: `openai = ["openai"]`, `anthropic = ["anthropic"]`, `langchain = ["langchain-core"]`, `litellm = ["litellm"]`, `all = ["openai", "anthropic", "langchain-core", "litellm"]`
  - Verify existing core dependencies have appropriate version constraints
  - Add Python version constraint: `python = "^3.11"`
  - _Requirements: 1.2, 1.3, 3.2_

- [x] 60. Configure plugin entry points in pyproject.toml
  - Add `[tool.poetry.plugins."prompt_manager.plugins"]` section
  - Register openai plugin: `openai = "prompt_manager.plugins.openai_plugin:OpenAIPlugin"`
  - Register anthropic plugin: `anthropic = "prompt_manager.plugins.anthropic_plugin:AnthropicPlugin"`
  - Register langchain plugin: `langchain = "prompt_manager.plugins.langchain_plugin:LangChainPlugin"`
  - Register litellm plugin: `litellm = "prompt_manager.plugins.litellm_plugin:LiteLLMPlugin"`
  - _Requirements: 1.2, 7.1_

- [x] 61. Update package metadata in pyproject.toml
  - Update name to "prompt-manager"
  - Set initial version to "0.1.0"
  - Add comprehensive description
  - Add authors with email
  - Add license = "MIT"
  - Add classifiers for PyPI (Python 3.11+, MIT license, Development Status :: 4 - Beta)
  - Add keywords for discoverability
  - Add homepage and repository URLs
  - _Requirements: 1.2_

- [x] 62. Configure package build settings
  - Add `tool.poetry.include` for py.typed marker
  - Add `tool.poetry.exclude` for test files, .git, __pycache__
  - Verify README.md is set as long_description
  - Set readme = "README.md"
  - Set packages = [{include = "prompt_manager", from = "src"}]
  - _Requirements: 6.1_

### Version Management
- [x] 63. Set version in single source of truth
  - Open `src/prompt_manager/__init__.py`
  - Set `__version__ = "0.1.0"`
  - Add to `__all__` exports
  - Update version in `pyproject.toml` to match
  - Document version sync requirement in RELEASING.md
  - _Requirements: 6.1_

### GitHub Actions - Testing
- [x] 64. Create GitHub Actions workflow for tests
  - Create `.github/workflows/test.yml`
  - Configure matrix for Python 3.11, 3.12
  - Add checkout and Python setup steps
  - Install Poetry and dependencies with all extras
  - Run unit tests with pytest
  - Run integration tests
  - Upload coverage reports
  - _Requirements: 6.3_

- [x] 65. Add linting and type checking to CI
  - Add job to run ruff linter
  - Add job to run black format checker
  - Add job to run mypy strict type checking
  - Configure jobs to run in parallel
  - Fail CI if any quality check fails
  - _Requirements: 3.3, 5.3, 6.3_

- [x] 66. Add security scanning to CI
  - Add job to run bandit security scanner
  - Add job to run safety dependency scanner
  - Configure to fail on high/critical vulnerabilities
  - Add scheduled weekly security scans
  - _Requirements: 6.3_

### GitHub Actions - Publishing
- [x] 67. Create GitHub Actions workflow for publishing
  - Create `.github/workflows/publish.yml`
  - Trigger on release published event
  - Add Python and Poetry setup
  - Run all tests before publishing
  - Build package with `poetry build`
  - Validate package contents
  - Publish to PyPI using POETRY_PYPI_TOKEN_PYPI secret
  - _Requirements: 6.3_

- [x] 68. Create GitHub Actions workflow for TestPyPI
  - Create `.github/workflows/test-publish.yml`
  - Trigger on release candidate tags (rc, beta, alpha)
  - Add Python and Poetry setup
  - Run all tests
  - Build package
  - Publish to TestPyPI using test credentials
  - _Requirements: 6.2, 6.3_

- [x] 69. Configure GitHub repository secrets
  - Generate PyPI API token at https://pypi.org/manage/account/token/
  - Add PYPI_TOKEN to GitHub repository secrets
  - Generate TestPyPI API token
  - Add TEST_PYPI_TOKEN to GitHub repository secrets
  - Document token setup in RELEASING.md
  - _Requirements: 6.2, 6.3_

### Dependency Management
- [x] 70. Configure Dependabot for automated updates
  - Create `.github/dependabot.yml`
  - Configure weekly dependency update checks for pip
  - Configure GitHub Actions updates
  - Set reviewers for automated PRs
  - Add update schedule for security patches
  - _Requirements: 1.3_

- [x] 71. Lock dependencies with Poetry
  - Run `poetry lock` to generate poetry.lock
  - Commit poetry.lock to repository
  - Verify lock file includes all dependencies with hashes
  - Document lock file usage in CONTRIBUTING.md
  - _Requirements: 1.3, 6.1_

### Build and Release Testing
- [x] 72. Test local package build
  - Run `poetry build` locally
  - Verify wheel and sdist created in dist/
  - Extract sdist and verify contents (includes py.typed, excludes tests)
  - Extract wheel and verify contents
  - Check file permissions are correct
  - _Requirements: 6.1_

- [x] 73. Test installation from local build
  - Create fresh virtual environment
  - Install from local wheel: `pip install dist/prompt_manager-0.1.0-py3-none-any.whl`
  - Test import: `import prompt_manager`
  - Test accessing __version__
  - Test importing integrations
  - Verify py.typed enables mypy type checking
  - _Requirements: 3.1, 6.1_

- [x] 74. Test editable installation
  - Create fresh virtual environment
  - Install with editable mode: `pip install -e .`
  - Verify changes to source code reflected without reinstall
  - Test all imports work
  - Test running tests from editable install
  - _Requirements: 3.1_

- [x] 75. Test installation with extras
  - Test `pip install .[openai]` installs openai SDK
  - Test `pip install .[anthropic]` installs anthropic SDK
  - Test `pip install .[langchain]` installs langchain-core
  - Test `pip install .[litellm]` installs litellm
  - Test `pip install .[all]` installs all frameworks
  - Verify error message when importing integration without extra installed
  - _Requirements: 3.2_

---

## Phase 6: Release and Publishing

### Pre-Release Preparation
- [x] 76. Create CHANGELOG.md
  - Create `CHANGELOG.md` in project root
  - Follow Keep a Changelog format
  - Add [Unreleased] section
  - Add [0.1.0] section with release date
  - List all features under "Added" section
  - Add framework integrations, documentation, examples, tests, CI/CD
  - Link to GitHub release page
  - _Requirements: 4.4_

- [x] 77. Final security audit
  - Run `bandit -r src/`
  - Run `safety check`
  - Review all dependencies for known vulnerabilities
  - Check that no API keys or secrets in code
  - Review .gitignore excludes sensitive files
  - Scan for hardcoded credentials
  - _Requirements: 6.1, 6.2_

- [x] 78. Final quality gate check
  - Run full test suite: `pytest`
  - Verify coverage ≥ 90%: `pytest --cov`
  - Run type checking: `mypy src/`
  - Run linting: `ruff check src/`
  - Run formatting check: `black --check src/`
  - Verify no warnings in test output
  - _Requirements: 5.1, 5.3, 6.1_

- [x] 79. Validate all documentation links
  - Check all links in README.md work
  - Check all links in CONTRIBUTING.md work
  - Check all links in RELEASING.md work
  - Check all links in docs/ work
  - Verify examples directory linked correctly
  - Test internal documentation references
  - _Requirements: 4.1, 4.2_

- [x] 80. Create release checklist issue
  - Create GitHub issue with pre-release checklist
  - Copy checklist from RELEASING.md
  - Check off each item as completed
  - Get approval from reviewers
  - Close issue when release published
  - _Requirements: 6.2_

### TestPyPI Release
- [x] 81. Build package for TestPyPI
  - Clean previous builds: `rm -rf dist/`
  - Build fresh: `poetry build`
  - Verify version number is correct
  - Inspect package contents
  - Check package size is reasonable
  - _Requirements: 6.1, 6.2_

- [x] 82. Publish to TestPyPI
  - Configure TestPyPI repository: `poetry config repositories.testpypi https://test.pypi.org/legacy/`
  - Publish: `poetry publish -r testpypi`
  - Verify upload successful
  - Check TestPyPI page for package listing
  - Verify metadata rendered correctly
  - _Requirements: 6.2_

- [x] 83. Test installation from TestPyPI
  - Create fresh virtual environment
  - Install from TestPyPI: `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ prompt-manager`
  - Test basic functionality
  - Test importing integrations
  - Run example code
  - Verify no issues
  - _Requirements: 6.2_

### PyPI Release
- [x] 84. Create Git tag for release
  - Ensure all changes committed
  - Create annotated tag: `git tag -a v0.1.0 -m "Release 0.1.0 - Initial production release"`
  - Push tag to GitHub: `git push origin v0.1.0`
  - Verify tag appears in GitHub
  - _Requirements: 6.2_

- [x] 85. Publish to PyPI
  - Build fresh: `poetry build`
  - Publish: `poetry publish`
  - Verify upload successful
  - Check PyPI page for package listing
  - Verify README rendered correctly
  - Check all metadata is correct
  - _Requirements: 6.2_

- [x] 86. Create GitHub release
  - Go to GitHub Releases page
  - Click "Draft a new release"
  - Select v0.1.0 tag
  - Set release title: "v0.1.0 - Initial Production Release"
  - Copy CHANGELOG.md entry to release notes
  - Add highlights and feature overview
  - Attach wheel and sdist files
  - Publish release
  - _Requirements: 6.2, 6.3_

### Post-Release Validation
- [x] 87. Verify PyPI installation
  - Create fresh virtual environment
  - Install from PyPI: `pip install prompt-manager`
  - Test import: `import prompt_manager`
  - Check __version__: `prompt_manager.__version__`
  - Test basic functionality with example code
  - _Requirements: 6.2_

- [x] 88. Test framework extras from PyPI
  - Test `pip install prompt-manager[openai]`
  - Test `pip install prompt-manager[anthropic]`
  - Test `pip install prompt-manager[langchain]`
  - Test `pip install prompt-manager[litellm]`
  - Test `pip install prompt-manager[all]`
  - Verify each extra installs correct dependencies
  - _Requirements: 3.2, 6.2_

- [x] 89. Verify GitHub Actions triggered correctly
  - Check that publish workflow ran on release
  - Verify all tests passed before publishing
  - Check CI badge status is passing
  - Review workflow logs for any warnings
  - _Requirements: 6.3_

- [x] 90. Monitor for immediate issues
  - Watch GitHub issues for bug reports
  - Monitor PyPI download stats
  - Check for installation errors in community channels
  - Set up alerts for critical issues
  - Prepare hotfix process if needed
  - _Requirements: 6.2_

### Documentation Updates
- [x] 91. Update documentation site (if applicable)
  - Deploy API documentation to docs site
  - Update version selector to include 0.1.0
  - Add release announcement to docs
  - Update getting started guide if needed
  - _Requirements: 4.1, 4.2_

- [x] 92. Announce release
  - Post announcement on project blog (if applicable)
  - Share on Twitter/social media
  - Post in relevant Python communities (r/Python, etc.)
  - Update project status from "beta" to "stable" if appropriate
  - _Requirements: 6.2_

---

## Success Criteria

### Automated Verification
**These criteria are verified by running tests and build tools:**

- [ ] All unit tests pass (`pytest tests/integrations/unit/`)
- [ ] All integration tests pass (`pytest tests/integrations/integration/`)
- [ ] All example validation tests pass (`pytest tests/integrations/examples/`)
- [ ] Code coverage ≥90% line coverage, ≥85% branch coverage (`pytest --cov`)
- [ ] No linting errors (`ruff check src/`)
- [ ] Code properly formatted (`black --check src/`)
- [ ] No type checking errors (`mypy --strict src/prompt_manager/integrations/`)
- [ ] Build completes successfully (`poetry build`)
- [ ] No security vulnerabilities (`bandit -r src/`, `safety check`)
- [ ] Package installs successfully from PyPI (`pip install prompt-manager`)
- [ ] All extras install correctly (`pip install prompt-manager[all]`)

### Manual Verification Required
**These criteria require human verification and will pause implementation:**

⚠️ **PAUSE POINT**: Once automated criteria pass, implementation pauses for manual review.

- [ ] Each framework integration example runs without errors
- [ ] OpenAI integration converts prompts correctly to OpenAI message format
- [ ] Anthropic integration handles system messages and alternation correctly
- [ ] LangChain integration converts Handlebars to f-string templates properly
- [ ] LiteLLM integration produces OpenAI-compatible format
- [ ] Error messages are clear and include install commands when dependencies missing
- [ ] Plugin auto-discovery loads all integrations on package import
- [ ] README examples are accurate and runnable
- [ ] Documentation is clear for developers at all experience levels
- [ ] PyPI package page renders correctly with description and badges
- [ ] Installation is straightforward with single pip command
- [ ] Type hints work correctly in VS Code and PyCharm (autocomplete shows)
- [ ] Package import time is < 500ms on modern hardware
- [ ] Integration conversion overhead is < 5ms

**How to Proceed**: After completing automated criteria, spec-execution-agent will pause and request user approval to continue based on manual verification.

---

## Notes

### Task Execution Strategy
- Tasks are designed to be completed sequentially within each phase
- Some tasks within a phase can be parallelized (e.g., different framework integrations)
- Each task should take 15-30 minutes to complete
- Tests are paired with implementation tasks for TDD approach
- Documentation tasks are separate phase to allow implementation to stabilize first

### Requirement Coverage
All 23 requirements from requirements.md are covered:
- **1.1-1.3**: Package Structure → Phase 1, Phase 5
- **2.1-2.5**: Framework Integrations → Phase 2
- **3.1-3.3**: Installation → Phase 5
- **4.1-4.4**: Documentation → Phase 3
- **5.1-5.3**: Testing → Phase 4
- **6.1-6.3**: Distribution → Phase 5, Phase 6
- **7.1-7.2**: Plugin System → Phase 2

### Dependencies Between Phases
- Phase 2 depends on Phase 1 (needs BaseIntegration)
- Phase 4 depends on Phase 2 (tests need implementations)
- Phase 5 depends on Phase 1-4 (CI tests need all code)
- Phase 6 depends on Phase 1-5 (release needs everything complete)

### Estimated Effort
- Phase 1: 1 week (core framework foundation)
- Phase 2: 1 week (4 framework integrations + plugins)
- Phase 3: 3-4 days (documentation and examples)
- Phase 4: 4-5 days (comprehensive test coverage)
- Phase 5: 3-4 days (CI/CD and build testing)
- Phase 6: 2-3 days (release preparation and publishing)

**Total: 4 weeks for complete implementation, testing, and release**
