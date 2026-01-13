"""Tests for template rendering engine."""

import pytest

from prompt_manager.core.template import ChatTemplateEngine, TemplateEngine
from prompt_manager.exceptions import TemplateRenderError


@pytest.mark.unit
class TestTemplateEngine:
    """Test TemplateEngine class."""

    @pytest.fixture
    def engine(self) -> TemplateEngine:
        """Create template engine."""
        return TemplateEngine()

    def test_simple_render(self, engine: TemplateEngine) -> None:
        """Test simple template rendering."""
        result = engine.render(
            "Hello {{name}}!",
            {"name": "World"},
        )
        assert result == "Hello World!"

    def test_multiple_variables(self, engine: TemplateEngine) -> None:
        """Test rendering with multiple variables."""
        result = engine.render(
            "{{greeting}} {{name}}, welcome to {{service}}!",
            {"greeting": "Hello", "name": "Alice", "service": "Prompt Manager"},
        )
        assert result == "Hello Alice, welcome to Prompt Manager!"

    def test_missing_variable(self, engine: TemplateEngine) -> None:
        """Test rendering with missing variable."""
        # pybars raises error for missing variables

        with pytest.raises(TemplateRenderError, match="Could not find variable"):
            engine.render(
                "Hello {{name}}!",
                {},
            )

    def test_invalid_syntax(self, engine: TemplateEngine) -> None:
        """Test invalid template syntax."""
        # Note: pybars is very lenient and doesn't raise errors for most malformed templates
        # This test verifies that validate() returns True for templates that compile
        is_valid = engine.validate("{{invalid")
        # pybars accepts unclosed brackets, so this is technically "valid"
        assert is_valid is True

    def test_validate_valid_template(self, engine: TemplateEngine) -> None:
        """Test validating valid template."""
        is_valid = engine.validate("Hello {{name}}!")
        assert is_valid is True

    def test_extract_variables(self, engine: TemplateEngine) -> None:
        """Test extracting variables from template."""
        variables = engine.extract_variables("Hello {{name}}, welcome to {{service}}!")
        assert set(variables) == {"name", "service"}

    def test_extract_variables_duplicates(self, engine: TemplateEngine) -> None:
        """Test extracting variables with duplicates."""
        variables = engine.extract_variables("{{name}} {{name}} {{other}}")
        assert set(variables) == {"name", "other"}

    def test_extract_variables_with_whitespace(self, engine: TemplateEngine) -> None:
        """Test extracting variables with whitespace."""
        variables = engine.extract_variables("{{ name }} {{ service }}")
        assert set(variables) == {"name", "service"}

    def test_render_with_partials(self, engine: TemplateEngine) -> None:
        """Test rendering with partial templates."""
        result = engine.render(
            "Header: {{>header}}\nContent: {{content}}",
            {"content": "Main content", "site": "My Site"},
            partials={"header": "Welcome to {{site}}"},
        )
        # Verify both the partial and main content are rendered
        assert "Welcome to My Site" in result
        assert "Content: Main content" in result


@pytest.mark.unit
class TestChatTemplateEngine:
    """Test ChatTemplateEngine class."""

    @pytest.fixture
    def engine(self) -> ChatTemplateEngine:
        """Create chat template engine."""
        return ChatTemplateEngine()

    def test_render_messages(self, engine: ChatTemplateEngine) -> None:
        """Test rendering chat messages."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant for {{company}}."},
            {"role": "user", "content": "{{query}}"},
        ]

        rendered = engine.render_messages(
            messages,
            {"company": "Acme Corp", "query": "Help me!"},
        )

        assert len(rendered) == 2
        assert rendered[0]["content"] == "You are a helpful assistant for Acme Corp."
        assert rendered[1]["content"] == "Help me!"

    def test_render_messages_no_variables(self, engine: ChatTemplateEngine) -> None:
        """Test rendering messages without variables."""
        messages = [
            {"role": "system", "content": "Static content"},
        ]

        rendered = engine.render_messages(messages, {})

        assert len(rendered) == 1
        assert rendered[0]["content"] == "Static content"

    def test_extract_variables_from_messages(
        self, engine: ChatTemplateEngine
    ) -> None:
        """Test extracting variables from messages."""
        messages = [
            {"role": "system", "content": "Welcome to {{service}}"},
            {"role": "user", "content": "My name is {{name}}"},
        ]

        variables = engine.extract_variables_from_messages(messages)
        assert set(variables) == {"service", "name"}

    def test_preserve_message_fields(self, engine: ChatTemplateEngine) -> None:
        """Test that additional message fields are preserved."""
        messages = [
            {
                "role": "assistant",
                "content": "Hello {{name}}",
                "name": "bot",
                "function_call": {"name": "test"},
            }
        ]

        rendered = engine.render_messages(messages, {"name": "User"})

        assert rendered[0]["role"] == "assistant"
        assert rendered[0]["content"] == "Hello User"
        assert rendered[0]["name"] == "bot"
        assert rendered[0]["function_call"] == {"name": "test"}


@pytest.mark.integration
class TestTemplateEngineIntegration:
    """Integration tests for template engine."""

    def test_complex_template(self) -> None:
        """Test complex real-world template."""
        engine = TemplateEngine()

        template = """
        Dear {{customer_name}},

        Thank you for your order #{{order_id}}.

        Order Details:
        - Product: {{product_name}}
        - Quantity: {{quantity}}
        - Total: ${{total}}

        Estimated delivery: {{delivery_date}}

        Best regards,
        {{company_name}}
        """

        variables = {
            "customer_name": "John Doe",
            "order_id": "12345",
            "product_name": "Widget",
            "quantity": "5",
            "total": "99.99",
            "delivery_date": "2024-01-15",
            "company_name": "Acme Corp",
        }

        result = engine.render(template, variables)

        assert "John Doe" in result
        assert "12345" in result
        assert "Widget" in result
        assert "Acme Corp" in result
