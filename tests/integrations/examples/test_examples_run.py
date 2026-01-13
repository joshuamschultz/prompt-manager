"""Test that example code imports and runs without errors."""

import importlib.util
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples" / "integrations"


@pytest.mark.integration
@pytest.mark.parametrize("example_file", [
    "openai_example.py",
    "anthropic_example.py",
    "langchain_example.py",
    "litellm_example.py",
    "custom_integration_example.py",
])
def test_example_imports(example_file):
    """Test that examples can be imported without errors."""
    example_path = EXAMPLES_DIR / example_file

    assert example_path.exists(), f"Example file not found: {example_path}"

    spec = importlib.util.spec_from_file_location("example", example_path)
    assert spec is not None

    module = importlib.util.module_from_spec(spec)
    # Import should not raise
    try:
        spec.loader.exec_module(module)
    except ImportError as e:
        # Allow import errors for optional dependencies in examples
        if "openai" in str(e) or "anthropic" in str(e) or "langchain" in str(e):
            pytest.skip(f"Optional dependency not installed: {e}")
        raise


@pytest.mark.integration
def test_examples_directory_exists():
    """Test that examples directory exists."""
    assert EXAMPLES_DIR.exists()
    assert EXAMPLES_DIR.is_dir()


@pytest.mark.integration
def test_all_expected_examples_present():
    """Test that all expected example files are present."""
    expected_files = [
        "openai_example.py",
        "anthropic_example.py",
        "langchain_example.py",
        "litellm_example.py",
        "custom_integration_example.py",
        "README.md",
        "requirements.txt",
    ]

    for filename in expected_files:
        assert (EXAMPLES_DIR / filename).exists(), f"Missing example file: {filename}"
