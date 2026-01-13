# Project Guide for Claude Code

## Publishing to PyPI

This package uses Poetry for dependency management and publishing.

### Automated Publishing (Recommended)

The project has GitHub Actions workflows configured for automated publishing:

1. **Via GitHub Release** (most common):
   ```bash
   # Create a new release on GitHub
   # The publish.yml workflow will automatically trigger
   # Token is stored in GitHub Secrets as PYPI_TOKEN
   ```

2. **Via Manual Workflow Dispatch**:
   - Go to GitHub Actions → Publish to PyPI workflow
   - Click "Run workflow"
   - Select target: `pypi` or `testpypi`
   - The workflow will build and publish

### Manual Publishing (Local)

If you need to publish manually from your local machine:

**Option 1: Using Poetry with Token**
```bash
# Set token as environment variable
export POETRY_PYPI_TOKEN_PYPI=pypi-your-token-here

# Build and publish
poetry build
poetry publish
```

**Option 2: Using Twine**
```bash
# Build with poetry
poetry build

# Publish with twine
twine upload dist/* --username __token__ --password pypi-your-token-here
```

**Option 3: Configure Poetry (persistent)**
```bash
# Store token in poetry config
poetry config pypi-token.pypi pypi-your-token-here

# Then just publish
poetry build
poetry publish
```

### Getting a PyPI Token

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Scope: Project → agentic-prompt-manager
4. Save the token securely

### Pre-Publish Checklist

Before publishing a new version:

1. **Update version in pyproject.toml**
   ```toml
   version = "0.1.0-beta.X"
   ```

2. **Update CHANGELOG.md**
   - Add release date
   - List all changes

3. **Run tests**
   ```bash
   poetry run pytest --no-cov tests/ \
     --ignore=tests/integration/test_async_workflow.py \
     --ignore=tests/integration/test_scenarios_async.py \
     --ignore=tests/integration/test_concurrent_access.py \
     --ignore=tests/integration/test_dual_mode.py \
     --ignore=tests/integration/test_error_handling.py \
     --ignore=tests/integrations/
   ```

4. **Build and verify**
   ```bash
   poetry build
   ls -lh dist/
   ```

5. **Commit and push**
   ```bash
   git add -A
   git commit -m "chore: release vX.Y.Z"
   git push origin master
   ```

6. **Create GitHub Release** (for automated publish)
   - Tag: `vX.Y.Z`
   - Title: `vX.Y.Z`
   - Description: Copy from CHANGELOG.md
   - Publish release → triggers workflow

## Project Structure

```
prompt-manager/
├── src/prompt_manager/     # Source code
├── tests/                  # Test suite
├── dist/                   # Built distributions (gitignored)
├── pyproject.toml          # Project config and dependencies
├── CHANGELOG.md            # Version history
├── README.md               # Package documentation
└── CLAUDE.md              # This file - project guide
```

## Development Workflow

### Install dependencies
```bash
poetry install --with dev -E all
```

### Run tests
```bash
# Core tests only (recommended for quick iteration)
poetry run pytest --no-cov tests/ \
  --ignore=tests/integration/test_async_workflow.py \
  --ignore=tests/integration/test_scenarios_async.py \
  --ignore=tests/integration/test_concurrent_access.py \
  --ignore=tests/integration/test_dual_mode.py \
  --ignore=tests/integration/test_error_handling.py \
  --ignore=tests/integrations/

# With coverage (slower)
poetry run pytest --cov=prompt_manager --cov-report=term-missing
```

### Linting and formatting
```bash
poetry run ruff check src/ tests/
poetry run black src/ tests/
poetry run mypy src/prompt_manager
```

### Clean build artifacts
```bash
rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

## GitHub Secrets Required

For automated publishing, these secrets must be set in GitHub repository settings:

- `PYPI_TOKEN` - PyPI API token for publishing releases

## Notes

- The package name on PyPI is `agentic-prompt-manager`
- Import name in Python is `prompt_manager`
- Supports Python 3.11+
- Beta releases use version format: `0.1.0-beta.X` (PyPI: `0.1.0bX`)
