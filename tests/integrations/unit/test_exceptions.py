"""Unit tests for integration exception classes."""

import pytest

from prompt_manager.exceptions import (
    IntegrationError,
    IntegrationNotAvailableError,
    ConversionError,
    IncompatibleFormatError,
    PromptManagerError,
)


class TestIntegrationError:
    """Test IntegrationError base class."""

    def test_is_prompt_manager_error(self) -> None:
        """Test that IntegrationError inherits from PromptManagerError."""
        error = IntegrationError("test error")
        assert isinstance(error, PromptManagerError)
        assert isinstance(error, IntegrationError)

    def test_message_stored(self) -> None:
        """Test that error message is properly stored."""
        error = IntegrationError("test message")
        assert error.message == "test message"
        assert str(error) == "test message"


class TestIntegrationNotAvailableError:
    """Test IntegrationNotAvailableError exception."""

    def test_message_formatting(self) -> None:
        """Test that error message includes install command."""
        error = IntegrationNotAvailableError("openai")
        msg = str(error)

        assert "openai" in msg
        assert "pip install agentic-prompt-manager[openai]" in msg

    def test_message_with_custom_extra(self) -> None:
        """Test error message with custom pip extra name."""
        error = IntegrationNotAvailableError("langchain", extra="langchain-core")
        msg = str(error)

        assert "langchain" in msg
        assert "pip install agentic-prompt-manager[langchain-core]" in msg

    def test_message_without_extra(self) -> None:
        """Test error message defaults to integration name for extra."""
        error = IntegrationNotAvailableError("anthropic")
        msg = str(error)

        assert "pip install agentic-prompt-manager[anthropic]" in msg

    def test_context_preserved(self) -> None:
        """Test that context information is preserved."""
        error = IntegrationNotAvailableError("openai", extra="openai-sdk")

        assert error.context["integration_name"] == "openai"
        assert error.context["extra"] == "openai-sdk"

    def test_inheritance(self) -> None:
        """Test exception inheritance hierarchy."""
        error = IntegrationNotAvailableError("test")

        assert isinstance(error, IntegrationError)
        assert isinstance(error, PromptManagerError)


class TestConversionError:
    """Test ConversionError exception."""

    def test_basic_error(self) -> None:
        """Test basic conversion error creation."""
        error = ConversionError("Failed to convert")

        assert "Failed to convert" in str(error)
        assert isinstance(error, IntegrationError)

    def test_with_prompt_id(self) -> None:
        """Test error with prompt ID context."""
        error = ConversionError(
            "Conversion failed",
            prompt_id="my_prompt",
        )

        assert error.context["prompt_id"] == "my_prompt"

    def test_with_framework(self) -> None:
        """Test error with framework context."""
        error = ConversionError(
            "Conversion failed",
            framework="openai",
        )

        assert error.context["framework"] == "openai"

    def test_with_cause(self) -> None:
        """Test error with underlying cause."""
        original = ValueError("Invalid value")
        error = ConversionError(
            "Conversion failed",
            cause=original,
        )

        assert error.__cause__ is original
        assert error.context["cause"] == "Invalid value"

    def test_full_context(self) -> None:
        """Test error with all context information."""
        original = TypeError("Wrong type")
        error = ConversionError(
            "Failed to convert prompt",
            prompt_id="test_prompt",
            framework="anthropic",
            cause=original,
        )

        assert error.context["prompt_id"] == "test_prompt"
        assert error.context["framework"] == "anthropic"
        assert error.context["cause"] == "Wrong type"
        assert error.__cause__ is original

    def test_serialization_for_logging(self) -> None:
        """Test that exception can be serialized for logging."""
        error = ConversionError(
            "Test error",
            prompt_id="test",
            framework="openai",
        )

        # Should be able to convert to string
        error_str = str(error)
        assert "Test error" in error_str

        # Context should be accessible
        assert error.context["prompt_id"] == "test"


class TestIncompatibleFormatError:
    """Test IncompatibleFormatError exception."""

    def test_basic_error(self) -> None:
        """Test basic format incompatibility error."""
        error = IncompatibleFormatError("TEXT", "anthropic")
        msg = str(error)

        assert "TEXT" in msg
        assert "anthropic" in msg
        assert "incompatible" in msg.lower()

    def test_with_supported_formats(self) -> None:
        """Test error message includes supported formats."""
        error = IncompatibleFormatError(
            "TEXT",
            "anthropic",
            supported_formats=["CHAT"],
        )
        msg = str(error)

        assert "TEXT" in msg
        assert "anthropic" in msg
        assert "CHAT" in msg
        assert "Supported formats" in msg

    def test_with_multiple_supported_formats(self) -> None:
        """Test error with multiple supported formats listed."""
        error = IncompatibleFormatError(
            "AUDIO",
            "openai",
            supported_formats=["TEXT", "CHAT"],
        )
        msg = str(error)

        assert "TEXT" in msg
        assert "CHAT" in msg
        assert "Supported formats" in msg

    def test_context_preservation(self) -> None:
        """Test that all context is preserved."""
        error = IncompatibleFormatError(
            "TEXT",
            "langchain",
            supported_formats=["CHAT", "TEMPLATE"],
        )

        assert error.context["prompt_format"] == "TEXT"
        assert error.context["framework"] == "langchain"
        assert error.context["supported_formats"] == ["CHAT", "TEMPLATE"]

    def test_inheritance(self) -> None:
        """Test exception inheritance."""
        error = IncompatibleFormatError("TEXT", "test")

        assert isinstance(error, IncompatibleFormatError)
        assert isinstance(error, IntegrationError)
        assert isinstance(error, PromptManagerError)


class TestExceptionHierarchy:
    """Test exception hierarchy and relationships."""

    def test_all_integration_errors_inherit_from_base(self) -> None:
        """Test that all integration exceptions inherit from IntegrationError."""
        exceptions = [
            IntegrationNotAvailableError("test"),
            ConversionError("test"),
            IncompatibleFormatError("TEXT", "test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, IntegrationError)
            assert isinstance(exc, PromptManagerError)

    def test_exception_can_be_caught_generically(self) -> None:
        """Test that integration exceptions can be caught with base class."""
        with pytest.raises(IntegrationError):
            raise IntegrationNotAvailableError("test")

        with pytest.raises(IntegrationError):
            raise ConversionError("test")

        with pytest.raises(IntegrationError):
            raise IncompatibleFormatError("TEXT", "test")

    def test_exception_can_be_caught_as_prompt_manager_error(self) -> None:
        """Test that integration exceptions can be caught as PromptManagerError."""
        with pytest.raises(PromptManagerError):
            raise IntegrationNotAvailableError("test")

        with pytest.raises(PromptManagerError):
            raise ConversionError("test")

        with pytest.raises(PromptManagerError):
            raise IncompatibleFormatError("TEXT", "test")


class TestExceptionMessages:
    """Test that exception messages are clear and actionable."""

    def test_integration_not_available_is_actionable(self) -> None:
        """Test that IntegrationNotAvailableError provides clear action."""
        error = IntegrationNotAvailableError("openai")
        msg = str(error)

        # Should tell user what's wrong
        assert "not available" in msg.lower()

        # Should tell user how to fix it
        assert "pip install" in msg
        assert "prompt-manager[openai]" in msg

    def test_conversion_error_is_descriptive(self) -> None:
        """Test that ConversionError describes the failure clearly."""
        error = ConversionError(
            "Failed to convert chat messages",
            prompt_id="my_prompt",
            framework="openai",
        )
        msg = str(error)

        # Should include the error description
        assert "Failed to convert chat messages" in msg

        # Context should be accessible for debugging
        assert error.context["prompt_id"] == "my_prompt"
        assert error.context["framework"] == "openai"

    def test_incompatible_format_suggests_alternatives(self) -> None:
        """Test that IncompatibleFormatError suggests valid alternatives."""
        error = IncompatibleFormatError(
            "TEXT",
            "anthropic",
            supported_formats=["CHAT"],
        )
        msg = str(error)

        # Should explain what went wrong
        assert "incompatible" in msg.lower()
        assert "TEXT" in msg

        # Should suggest what formats work
        assert "Supported formats" in msg
        assert "CHAT" in msg
