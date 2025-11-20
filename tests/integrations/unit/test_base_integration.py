"""Unit tests for BaseIntegration abstract class."""

import pytest

from prompt_manager.core.models import Prompt, PromptFormat, PromptStatus, PromptTemplate
from prompt_manager.core.template import TemplateEngine
from prompt_manager.integrations.base import BaseIntegration


class ConcreteIntegration(BaseIntegration[str]):
    """Concrete implementation of BaseIntegration for testing."""

    async def convert(self, prompt: Prompt, variables: dict[str, object]) -> str:
        """Convert prompt to string format."""
        # Simple implementation for testing
        content = prompt.template.content if prompt.template else ""
        rendered = await self._template_engine.render(content, variables)
        return str(rendered)

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is TEXT format."""
        return prompt.format == PromptFormat.TEXT


class TestBaseIntegration:
    """Test BaseIntegration abstract class."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that BaseIntegration cannot be instantiated directly."""
        engine = TemplateEngine()

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseIntegration(engine)  # type: ignore[abstract]

    def test_concrete_subclass_can_be_instantiated(self) -> None:
        """Test that concrete subclasses can be instantiated."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine)

        assert isinstance(integration, BaseIntegration)
        assert isinstance(integration, ConcreteIntegration)

    def test_template_engine_property(self) -> None:
        """Test that template_engine property returns the engine."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine)

        assert integration.template_engine is engine

    def test_strict_validation_property_default(self) -> None:
        """Test that strict_validation defaults to True."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine)

        assert integration.strict_validation is True

    def test_strict_validation_property_explicit(self) -> None:
        """Test that strict_validation can be set explicitly."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine, strict_validation=False)

        assert integration.strict_validation is False

    def test_abstract_methods_must_be_implemented(self) -> None:
        """Test that abstract methods raise NotImplementedError if not overridden."""

        class IncompleteIntegration(BaseIntegration[str]):
            """Integration with missing implementations."""

            # Missing convert() and validate_compatibility()

        engine = TemplateEngine()

        # Python will raise TypeError because abstract methods aren't implemented
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteIntegration(engine)  # type: ignore[abstract]


class TestConcreteIntegration:
    """Test the concrete integration implementation used for testing."""

    @pytest.fixture
    def engine(self) -> TemplateEngine:
        """Create a TemplateEngine instance."""
        return TemplateEngine()

    @pytest.fixture
    def integration(self, engine: TemplateEngine) -> ConcreteIntegration:
        """Create a ConcreteIntegration instance."""
        return ConcreteIntegration(engine)

    @pytest.fixture
    def text_prompt(self) -> Prompt:
        """Create a simple TEXT format prompt."""
        return Prompt(
            id="test_prompt",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content="Hello {{name}}!",
                variables=["name"],
            ),
        )

    @pytest.mark.asyncio
    async def test_convert_renders_template(
        self,
        integration: ConcreteIntegration,
        text_prompt: Prompt,
    ) -> None:
        """Test that convert() renders the template with variables."""
        result = await integration.convert(text_prompt, {"name": "Alice"})

        assert result == "Hello Alice!"

    @pytest.mark.asyncio
    async def test_convert_with_multiple_variables(
        self,
        integration: ConcreteIntegration,
    ) -> None:
        """Test convert() with multiple variables."""
        prompt = Prompt(
            id="multi_var",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content="{{greeting}} {{name}}, welcome to {{place}}!",
                variables=["greeting", "name", "place"],
            ),
        )

        result = await integration.convert(
            prompt,
            {"greeting": "Hi", "name": "Bob", "place": "Wonderland"},
        )

        assert result == "Hi Bob, welcome to Wonderland!"

    def test_validate_compatibility_accepts_text_format(
        self,
        integration: ConcreteIntegration,
        text_prompt: Prompt,
    ) -> None:
        """Test that validate_compatibility() accepts TEXT format."""
        assert integration.validate_compatibility(text_prompt) is True

    def test_validate_compatibility_rejects_chat_format(
        self,
        integration: ConcreteIntegration,
    ) -> None:
        """Test that validate_compatibility() rejects CHAT format."""
        from prompt_manager.core.models import ChatPromptTemplate, Message, Role

        chat_prompt = Prompt(
            id="chat_prompt",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="test"),
                ],
                variables=[],
            ),
        )

        assert integration.validate_compatibility(chat_prompt) is False

    def test_strict_validation_mode(self, engine: TemplateEngine) -> None:
        """Test strict validation mode configuration."""
        strict_integration = ConcreteIntegration(engine, strict_validation=True)
        lenient_integration = ConcreteIntegration(engine, strict_validation=False)

        assert strict_integration.strict_validation is True
        assert lenient_integration.strict_validation is False


class TestGenericTypeParameter:
    """Test that BaseIntegration supports different generic type parameters."""

    def test_generic_with_string_type(self) -> None:
        """Test integration with string output type."""

        class StringIntegration(BaseIntegration[str]):
            async def convert(self, prompt: Prompt, variables: dict[str, object]) -> str:
                return "string result"

            def validate_compatibility(self, prompt: Prompt) -> bool:
                return True

        engine = TemplateEngine()
        integration = StringIntegration(engine)

        assert isinstance(integration, BaseIntegration)

    def test_generic_with_list_type(self) -> None:
        """Test integration with list output type."""

        class ListIntegration(BaseIntegration[list[dict[str, object]]]):
            async def convert(
                self,
                prompt: Prompt,
                variables: dict[str, object],
            ) -> list[dict[str, object]]:
                return [{"role": "user", "content": "test"}]

            def validate_compatibility(self, prompt: Prompt) -> bool:
                return True

        engine = TemplateEngine()
        integration = ListIntegration(engine)

        assert isinstance(integration, BaseIntegration)

    def test_generic_with_dict_type(self) -> None:
        """Test integration with dict output type."""

        class DictIntegration(BaseIntegration[dict[str, object]]):
            async def convert(
                self,
                prompt: Prompt,
                variables: dict[str, object],
            ) -> dict[str, object]:
                return {"system": "test", "messages": []}

            def validate_compatibility(self, prompt: Prompt) -> bool:
                return True

        engine = TemplateEngine()
        integration = DictIntegration(engine)

        assert isinstance(integration, BaseIntegration)


class TestInitializationParameters:
    """Test initialization parameters and their effects."""

    def test_init_with_required_template_engine(self) -> None:
        """Test that template_engine is required."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine)

        assert integration.template_engine is engine

    def test_init_with_strict_validation_true(self) -> None:
        """Test initialization with strict_validation=True."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine, strict_validation=True)

        assert integration.strict_validation is True

    def test_init_with_strict_validation_false(self) -> None:
        """Test initialization with strict_validation=False."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine, strict_validation=False)

        assert integration.strict_validation is False

    def test_template_engine_stored_correctly(self) -> None:
        """Test that template engine is stored and accessible."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine)

        # Verify the engine is stored
        assert integration.template_engine is engine
        assert integration._template_engine is engine

    def test_strict_validation_stored_correctly(self) -> None:
        """Test that strict_validation is stored and accessible."""
        engine = TemplateEngine()
        integration = ConcreteIntegration(engine, strict_validation=False)

        # Verify the flag is stored
        assert integration.strict_validation is False
        assert integration._strict_validation is False
