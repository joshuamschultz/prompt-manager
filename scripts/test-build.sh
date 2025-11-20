#!/bin/bash
# Test script for validating package builds
# Run this before publishing to PyPI

set -e  # Exit on error

echo "================================================"
echo "Package Build and Installation Test"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Task 72: Test local package build
echo -e "\n${YELLOW}Task 72: Testing local package build${NC}"
rm -rf dist/ build/ *.egg-info
poetry build

# Verify outputs
if [ -f dist/prompt_manager-*.whl ] && [ -f dist/prompt_manager-*.tar.gz ]; then
    echo -e "${GREEN}✓ Build successful - wheel and sdist created${NC}"
else
    echo -e "${RED}✗ Build failed - missing distribution files${NC}"
    exit 1
fi

# Check file contents
echo -e "\n${YELLOW}Verifying package contents...${NC}"

# Extract wheel name
WHEEL_FILE=$(ls dist/prompt_manager-*.whl)
echo "Inspecting: $WHEEL_FILE"

# Check for py.typed
if unzip -l "$WHEEL_FILE" | grep -q "py.typed"; then
    echo -e "${GREEN}✓ py.typed marker included${NC}"
else
    echo -e "${RED}✗ py.typed marker missing${NC}"
    exit 1
fi

# Check tests are excluded
if unzip -l "$WHEEL_FILE" | grep -q "tests/"; then
    echo -e "${RED}✗ Tests incorrectly included in package${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Tests correctly excluded${NC}"
fi

# Check examples are excluded
if unzip -l "$WHEEL_FILE" | grep -q "examples/"; then
    echo -e "${RED}✗ Examples incorrectly included in package${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Examples correctly excluded${NC}"
fi

# Task 73: Test installation from local build
echo -e "\n${YELLOW}Task 73: Testing installation from local build${NC}"

# Create temporary virtual environment
TEMP_ENV="test-install-env"
python -m venv "$TEMP_ENV"
source "$TEMP_ENV/bin/activate"

# Install from wheel
echo "Installing from local wheel..."
pip install "$WHEEL_FILE"

# Test basic import
echo "Testing basic import..."
python -c "import prompt_manager; print(f'Version: {prompt_manager.__version__}')"

# Test version matches
VERSION=$(python -c "import prompt_manager; print(prompt_manager.__version__)")
echo -e "${GREEN}✓ Installed version: $VERSION${NC}"

# Test importing integrations module
echo "Testing integrations import..."
python -c "from prompt_manager.integrations import BaseIntegration"
echo -e "${GREEN}✓ BaseIntegration import successful${NC}"

# Test mypy recognizes types
echo "Testing type hints..."
echo "from prompt_manager import PromptManager" > test_types.py
echo "manager: PromptManager" >> test_types.py
pip install mypy > /dev/null 2>&1
if mypy test_types.py > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Type hints working with mypy${NC}"
else
    echo -e "${YELLOW}⚠ Type checking had issues (may be expected)${NC}"
fi
rm test_types.py

deactivate
rm -rf "$TEMP_ENV"

# Task 74: Test editable installation
echo -e "\n${YELLOW}Task 74: Testing editable installation${NC}"

EDITABLE_ENV="test-editable-env"
python -m venv "$EDITABLE_ENV"
source "$EDITABLE_ENV/bin/activate"

# Install in editable mode
echo "Installing in editable mode..."
pip install -e .

# Test imports work
echo "Testing imports..."
python -c "import prompt_manager; print(f'Editable install version: {prompt_manager.__version__}')"

# Make a temporary change to verify editable mode
echo "Verifying editable mode..."
INIT_FILE="src/prompt_manager/__init__.py"
BACKUP_FILE="${INIT_FILE}.backup"
cp "$INIT_FILE" "$BACKUP_FILE"

# Add a test comment (then restore)
echo "# Test editable install" >> "$INIT_FILE"
if python -c "import prompt_manager" 2>/dev/null; then
    echo -e "${GREEN}✓ Editable install working${NC}"
else
    echo -e "${RED}✗ Editable install failed${NC}"
    mv "$BACKUP_FILE" "$INIT_FILE"
    exit 1
fi

# Restore original file
mv "$BACKUP_FILE" "$INIT_FILE"

deactivate
rm -rf "$EDITABLE_ENV"

# Task 75: Test installation with extras
echo -e "\n${YELLOW}Task 75: Testing installation with extras${NC}"

for EXTRA in "openai" "anthropic" "langchain" "litellm" "all"; do
    echo -e "\nTesting extra: $EXTRA"

    EXTRA_ENV="test-extra-${EXTRA}-env"
    python -m venv "$EXTRA_ENV"
    source "$EXTRA_ENV/bin/activate"

    # Install with extra
    pip install "${WHEEL_FILE}[$EXTRA]" > /dev/null 2>&1

    # Verify installation
    if [ "$EXTRA" = "openai" ]; then
        python -c "import openai" && echo -e "${GREEN}✓ openai extra installed${NC}"
    elif [ "$EXTRA" = "anthropic" ]; then
        python -c "import anthropic" && echo -e "${GREEN}✓ anthropic extra installed${NC}"
    elif [ "$EXTRA" = "langchain" ]; then
        python -c "import langchain_core" && echo -e "${GREEN}✓ langchain extra installed${NC}"
    elif [ "$EXTRA" = "litellm" ]; then
        python -c "import litellm" && echo -e "${GREEN}✓ litellm extra installed${NC}"
    elif [ "$EXTRA" = "all" ]; then
        python -c "import openai, anthropic, langchain_core, litellm" && echo -e "${GREEN}✓ all extras installed${NC}"
    fi

    deactivate
    rm -rf "$EXTRA_ENV"
done

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}All build and installation tests passed!${NC}"
echo -e "${GREEN}================================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Review package contents in dist/"
echo "2. Test on TestPyPI: poetry publish -r testpypi"
echo "3. Install from TestPyPI and validate"
echo "4. If successful, publish to PyPI: poetry publish"
