"""Tests for core Pydantic models."""

import pytest
from pydantic import ValidationError

from prompt_manager.core.models import (
    ChatPromptTemplate,
    Message,
    Prompt,
    PromptFormat,
    PromptMetadata,
    PromptStatus,
    PromptTemplate,
    Role,
)


class TestMessage:
    """Test Message model."""

    def test_valid_message(self) -> None:
        """Test creating a valid message."""
        msg = Message(role=Role.USER, content="Hello")
        assert msg.role == Role.USER
        assert msg.content == "Hello"

    def test_empty_content_fails(self) -> None:
        """Test that empty content fails validation."""
        with pytest.raises(ValidationError):
            Message(role=Role.USER, content="   ")

    def test_message_immutable(self) -> None:
        """Test that messages are immutable."""
        msg = Message(role=Role.USER, content="Hello")
        with pytest.raises(ValidationError):
            msg.content = "New content"  # type: ignore


class TestPromptMetadata:
    """Test PromptMetadata model."""

    def test_default_values(self) -> None:
        """Test default values."""
        metadata = PromptMetadata()
        assert metadata.tags == []
        assert metadata.use_cases == []
        assert metadata.custom == {}

    def test_tag_normalization(self) -> None:
        """Test that tags are normalized."""
        metadata = PromptMetadata(tags=["Test", "  Another ", ""])
        assert metadata.tags == ["test", "another"]

    def test_temperature_validation(self) -> None:
        """Test temperature range validation."""
        metadata = PromptMetadata(temperature=0.5)
        assert metadata.temperature == 0.5

        with pytest.raises(ValidationError):
            PromptMetadata(temperature=3.0)

        with pytest.raises(ValidationError):
            PromptMetadata(temperature=-0.1)


class TestPromptTemplate:
    """Test PromptTemplate model."""

    def test_valid_template(self) -> None:
        """Test creating a valid template."""
        template = PromptTemplate(
            content="Hello {{name}}",
            variables=["name"],
        )
        assert template.content == "Hello {{name}}"
        assert template.variables == ["name"]

    def test_empty_content_fails(self) -> None:
        """Test that empty content fails."""
        with pytest.raises(ValidationError):
            PromptTemplate(content="   ", variables=[])

    def test_invalid_variable_names(self) -> None:
        """Test that invalid variable names fail."""
        with pytest.raises(ValidationError):
            PromptTemplate(
                content="Test",
                variables=["valid", "123invalid"],
            )


class TestPrompt:
    """Test Prompt model."""

    def test_valid_text_prompt(self, simple_prompt: Prompt) -> None:
        """Test creating a valid text prompt."""
        assert simple_prompt.id == "test_greeting"
        assert simple_prompt.format == PromptFormat.TEXT
        assert simple_prompt.template is not None

    def test_valid_chat_prompt(self, chat_prompt: Prompt) -> None:
        """Test creating a valid chat prompt."""
        assert chat_prompt.id == "test_chat"
        assert chat_prompt.format == PromptFormat.CHAT
        assert chat_prompt.chat_template is not None

    def test_version_validation(self) -> None:
        """Test semantic version validation."""
        prompt = Prompt(
            id="test",
            version="1.2.3",
            format=PromptFormat.TEXT,
            template=PromptTemplate(content="Test", variables=[]),
        )
        assert prompt.version == "1.2.3"

        with pytest.raises(ValidationError):
            Prompt(
                id="test",
                version="invalid",
                format=PromptFormat.TEXT,
                template=PromptTemplate(content="Test", variables=[]),
            )

    def test_template_format_mismatch_fails(self) -> None:
        """Test that template format must match prompt format."""
        # Chat format requires chat_template
        with pytest.raises(ValidationError):
            Prompt(
                id="test",
                format=PromptFormat.CHAT,
                template=PromptTemplate(content="Test", variables=[]),
            )

        # Text format requires template
        with pytest.raises(ValidationError):
            Prompt(
                id="test",
                format=PromptFormat.TEXT,
                chat_template=ChatPromptTemplate(
                    messages=[Message(role=Role.USER, content="Test")],
                    variables=[],
                ),
            )

    def test_bump_version_patch(self, simple_prompt: Prompt) -> None:
        """Test bumping patch version."""
        new_version = simple_prompt.bump_version("patch")
        assert new_version == "1.0.1"
        assert simple_prompt.version == "1.0.1"

    def test_bump_version_minor(self, simple_prompt: Prompt) -> None:
        """Test bumping minor version."""
        new_version = simple_prompt.bump_version("minor")
        assert new_version == "1.1.0"

    def test_bump_version_major(self, simple_prompt: Prompt) -> None:
        """Test bumping major version."""
        new_version = simple_prompt.bump_version("major")
        assert new_version == "2.0.0"

    def test_get_variables(self, simple_prompt: Prompt, chat_prompt: Prompt) -> None:
        """Test getting template variables."""
        assert simple_prompt.get_variables() == ["name", "service"]
        assert chat_prompt.get_variables() == ["company", "user_query"]


@pytest.mark.unit
class TestPromptStatus:
    """Test PromptStatus enum."""

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert PromptStatus.DRAFT.value == "draft"
        assert PromptStatus.ACTIVE.value == "active"
        assert PromptStatus.DEPRECATED.value == "deprecated"
        assert PromptStatus.ARCHIVED.value == "archived"


@pytest.mark.unit
class TestPromptFormat:
    """Test PromptFormat enum."""

    def test_format_values(self) -> None:
        """Test format enum values."""
        assert PromptFormat.TEXT.value == "text"
        assert PromptFormat.CHAT.value == "chat"
        assert PromptFormat.COMPLETION.value == "completion"
        assert PromptFormat.INSTRUCTION.value == "instruction"
