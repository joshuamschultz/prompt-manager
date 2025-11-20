# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-01-19

### Added

- **Framework Integrations**: Seamless integration with popular LLM frameworks
  - OpenAI SDK integration with support for chat and completion formats
  - Anthropic SDK (Claude) integration with system message handling and message alternation validation
  - LangChain integration with PromptTemplate and ChatPromptTemplate support
  - LiteLLM integration for multi-provider support

- **Plugin System**: Auto-discovery and registration of framework integrations
  - Entry point-based plugin discovery
  - Lazy loading for optimal performance
  - Graceful handling of missing optional dependencies

- **Type Safety**: Full type hint coverage with PEP 561 support
  - `py.typed` marker file for distributed type hints
  - TypedDict definitions for message formats
  - Strict mypy validation

- **Documentation**:
  - Comprehensive README with installation instructions and examples
  - CONTRIBUTING.md with development setup guide
  - RELEASING.md with release process documentation
  - SECURITY.md with vulnerability reporting instructions
  - Integration guide (docs/INTEGRATION_GUIDE.md) for custom integrations
  - Complete examples for all framework integrations

- **Examples**: Working code examples for all integrations
  - OpenAI SDK integration example
  - Anthropic SDK integration example
  - LangChain integration example
  - LiteLLM integration example
  - Custom integration example

- **Testing**: Comprehensive test suite
  - Unit tests for all integration classes (90%+ coverage)
  - Integration tests with mocked API calls
  - Example validation tests
  - Type checking validation
  - Performance benchmarks

- **CI/CD**: Automated workflows for quality and publishing
  - GitHub Actions workflow for testing (Python 3.11, 3.12)
  - Automated linting, formatting, and type checking
  - Security scanning (bandit, safety)
  - TestPyPI and PyPI publishing workflows
  - Dependabot for automated dependency updates

- **Package Distribution**:
  - PyPI-ready package configuration
  - Optional extras for framework dependencies (`[openai]`, `[anthropic]`, `[langchain]`, `[litellm]`, `[all]`)
  - Proper versioning and metadata
  - MIT license

- **Error Handling**: Clear, actionable error messages
  - `IntegrationNotAvailableError` with install commands when optional dependencies missing
  - `ConversionError` for prompt conversion failures
  - `IncompatibleFormatError` for format mismatches

### Infrastructure

- Python 3.11+ support with modern typing features
- Poetry for dependency management and publishing
- Comprehensive pre-commit hooks
- Security scanning in CI pipeline
- Weekly automated dependency updates

[unreleased]: https://github.com/prompt-manager/prompt-manager/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/prompt-manager/prompt-manager/releases/tag/v0.1.0
