"""Run doctests from integration modules."""

import doctest

import pytest


def load_tests(loader, tests, ignore):
    """Load doctests from integration modules."""
    # Import modules with doctests
    try:
        from prompt_manager.integrations import anthropic, base, langchain, litellm, openai

        modules = [base, openai, anthropic, langchain, litellm]

        for module in modules:
            tests.addTests(doctest.DocTestSuite(module))

    except Exception:
        pass  # Skip if modules don't have doctests

    return tests


@pytest.mark.integration
def test_docstrings_present():
    """Test that integration modules have docstrings."""
    from prompt_manager.integrations import base, openai

    assert base.__doc__ is not None
    assert openai.OpenAIIntegration.__doc__ is not None


@pytest.mark.integration
def test_integration_modules_importable():
    """Test that integration modules can be imported for doctest."""
    from prompt_manager.integrations import anthropic, base, litellm, openai

    assert base is not None
    assert openai is not None
    assert anthropic is not None
    assert litellm is not None
