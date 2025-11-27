"""
Template rendering engine using Handlebars (pybars4).

Provides template rendering with variable extraction and validation.
"""

import re
from collections.abc import Mapping
from typing import Any

from pybars import Compiler

from prompt_manager.exceptions import TemplateError, TemplateRenderError, TemplateSyntaxError


class TemplateEngine:
    """
    Handlebars template engine.

    Implements TemplateEngineProtocol for dependency injection.
    """

    def __init__(self) -> None:
        """Initialize the template engine."""
        self._compiler = Compiler()
        self._variable_pattern = re.compile(r"\{\{([^}]+)\}\}")

    def render(
        self,
        template: str,
        variables: Mapping[str, Any],
        *,
        partials: Mapping[str, str] | None = None,
    ) -> str:
        """
        Render a Handlebars template with variables.

        Args:
            template: Handlebars template string
            variables: Variables for rendering
            partials: Optional partial templates

        Returns:
            Rendered string

        Raises:
            TemplateRenderError: If rendering fails
            TemplateSyntaxError: If template syntax is invalid

        Example:
            >>> engine = TemplateEngine()
            >>> result = engine.render("Hello {{name}}", {"name": "World"})
            >>> print(result)
            Hello World
        """
        try:
            # Validate template syntax first
            self.validate(template)

            # Compile template
            compiled_template = self._compiler.compile(template)

            # Prepare partials if provided
            compiled_partials = {}
            if partials:
                for name, partial_template in partials.items():
                    try:
                        compiled_partials[name] = self._compiler.compile(partial_template)
                    except Exception as e:
                        raise TemplateSyntaxError(
                            f"Invalid partial '{name}': {e}",
                            partial=name,
                        ) from e

            # Render with variables and partials
            rendered = compiled_template(variables, partials=compiled_partials)

            # Handle None result
            if rendered is None:
                msg = "Template rendering returned None"
                raise TemplateError(msg)

            return str(rendered)

        except TemplateSyntaxError:
            raise
        except Exception as e:
            raise TemplateRenderError(template, dict(variables), e) from e

    def validate(self, template: str) -> bool:
        """
        Validate Handlebars template syntax.

        Args:
            template: Template string to validate

        Returns:
            True if valid

        Raises:
            TemplateSyntaxError: If template is invalid

        Example:
            >>> engine = TemplateEngine()
            >>> is_valid = engine.validate("{{name}}")
            >>> print(is_valid)
            True
        """
        try:
            self._compiler.compile(template)
            return True
        except Exception as e:
            raise TemplateSyntaxError(
                f"Invalid template syntax: {e}",
                template=template,
            ) from e

    def extract_variables(self, template: str) -> list[str]:
        """
        Extract variable names from Handlebars template.

        This is a basic implementation that extracts simple variable references.
        It doesn't handle complex helpers or nested paths.

        Args:
            template: Template string

        Returns:
            List of unique variable names
        """
        # Find all {{...}} patterns
        matches = self._variable_pattern.findall(template)

        variables = set()
        for match in matches:
            # Clean up the match (remove whitespace, helpers, etc.)
            cleaned = match.strip()

            # Skip built-in helpers
            if cleaned.startswith("#") or cleaned.startswith("/") or cleaned.startswith("!"):
                continue

            # Handle helper calls - extract first argument
            if " " in cleaned:
                parts = cleaned.split()
                # First part might be a helper, second might be variable
                if not parts[0].startswith("@"):  # Skip special variables
                    variables.add(parts[0])
                if len(parts) > 1 and not parts[1].startswith("@"):
                    variables.add(parts[1])
            else:
                # Simple variable reference
                if not cleaned.startswith("@"):  # Skip special variables like @root
                    # Handle dot notation - take the first part
                    first_part = cleaned.split(".")[0]
                    if first_part:
                        variables.add(first_part)

        return sorted(variables)

    def register_helper(self, name: str, helper_fn: Any) -> None:
        """
        Register a custom Handlebars helper.

        Args:
            name: Helper name
            helper_fn: Helper function

        Example:
            >>> engine = TemplateEngine()
            >>> engine.register_helper('upper', lambda this, text: text.upper())
            >>> engine.render('{{upper name}}', {'name': 'john'})
            'JOHN'
        """
        # Note: pybars4 doesn't have a direct register_helper API
        # Helpers need to be passed during compilation or rendering
        # This method is here for API consistency but implementation
        # would require extending pybars4 or using a wrapper
        msg = (
            "Custom helpers not yet implemented. "
            "Pass helpers via partials parameter for now."
        )
        raise NotImplementedError(msg)


class ChatTemplateEngine:
    """
    Template engine for chat-based prompts.

    Handles message-level templating and role-based rendering.
    """

    def __init__(self) -> None:
        """Initialize chat template engine."""
        self._template_engine = TemplateEngine()

    def render_messages(
        self,
        messages: list[dict[str, Any]],
        variables: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Render a list of chat messages.

        Args:
            messages: List of message dictionaries with role and content
            variables: Variables for rendering

        Returns:
            List of rendered messages

        Raises:
            TemplateRenderError: If rendering fails

        Example:
            >>> engine = ChatTemplateEngine()
            >>> messages = [{"role": "user", "content": "Hello {{name}}"}]
            >>> result = engine.render_messages(messages, {"name": "World"})
            >>> print(result)
            [{'role': 'user', 'content': 'Hello World'}]
        """
        rendered_messages = []

        for msg in messages:
            role = msg.get("role")
            content_template = msg.get("content", "")

            # Render content if it contains variables
            if "{{" in content_template:
                rendered_content = self._template_engine.render(
                    content_template,
                    variables,
                )
            else:
                rendered_content = content_template

            rendered_msg = {
                "role": role,
                "content": rendered_content,
            }

            # Preserve additional fields
            for key, value in msg.items():
                if key not in ("role", "content"):
                    rendered_msg[key] = value

            rendered_messages.append(rendered_msg)

        return rendered_messages

    def extract_variables_from_messages(
        self,
        messages: list[dict[str, Any]],
    ) -> list[str]:
        """
        Extract variables from all messages.

        Args:
            messages: List of message dictionaries

        Returns:
            List of unique variable names
        """
        all_variables = set()

        for msg in messages:
            content = msg.get("content", "")
            if "{{" in content:
                variables = self._template_engine.extract_variables(content)
                all_variables.update(variables)

        return sorted(all_variables)
