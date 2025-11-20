# Release Process

This document outlines the step-by-step process for releasing new versions of Prompt Manager to PyPI.

## Pre-Release Checklist

Before starting the release process, ensure all of the following are complete:

- [ ] All tests passing (`pytest`)
- [ ] Code coverage >= 90% line coverage, >= 85% branch coverage (`pytest --cov`)
- [ ] Type checking passes (`mypy --strict src/`)
- [ ] Linting passes (`ruff check src/`)
- [ ] Code formatting passes (`black --check src/`)
- [ ] Security scans pass (`bandit -r src/`, `safety check`)
- [ ] CHANGELOG.md updated with all changes
- [ ] Version bumped in both `src/prompt_manager/__init__.py` and `pyproject.toml`
- [ ] README examples tested and working
- [ ] Integration examples tested (`pytest tests/integrations/examples/`)
- [ ] Documentation reviewed and updated
- [ ] Breaking changes documented (if any)
- [ ] Migration guide updated (if breaking changes)

## Version Numbering

Prompt Manager follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes that require user code modifications
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

**Pre-release versions**:
- `0.1.0-alpha.1`: Early testing, unstable
- `0.1.0-beta.1`: Feature complete, testing phase
- `0.1.0-rc.1`: Release candidate, final testing

## Release Steps

### 1. Update Version Numbers

Update the version in both locations (must match):

**File: `src/prompt_manager/__init__.py`**
```python
__version__ = "X.Y.Z"
```

**File: `pyproject.toml`**
```toml
[tool.poetry]
version = "X.Y.Z"
```

Commit the version change:
```bash
git add src/prompt_manager/__init__.py pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
git push origin main
```

### 2. Update CHANGELOG

Update `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature descriptions

### Changed
- Changes in existing functionality

### Fixed
- Bug fixes

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Security
- Security fixes or improvements
```

Move items from `[Unreleased]` to the new version section.

Commit the changelog:
```bash
git add CHANGELOG.md
git commit -m "docs: update changelog for X.Y.Z"
git push origin main
```

### 3. Run Final Quality Checks

```bash
# Run full test suite
pytest

# Check coverage
pytest --cov=prompt_manager --cov-report=term-missing

# Type checking
mypy --strict src/

# Linting
ruff check src/

# Formatting
black --check src/

# Security
bandit -r src/
safety check

# Or run all checks together
make ci
```

Ensure all checks pass before continuing.

### 4. Build Package

Clean previous builds and create fresh distribution:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build with Poetry
poetry build

# Verify build output
ls -lh dist/
```

You should see two files:
- `prompt_manager-X.Y.Z-py3-none-any.whl` (wheel)
- `prompt_manager-X.Y.Z.tar.gz` (source distribution)

### 5. Inspect Package Contents

Verify the package includes correct files:

```bash
# Inspect wheel contents
unzip -l dist/prompt_manager-X.Y.Z-py3-none-any.whl

# Verify py.typed is included
unzip -l dist/prompt_manager-X.Y.Z-py3-none-any.whl | grep py.typed

# Verify tests are NOT included
unzip -l dist/prompt_manager-X.Y.Z-py3-none-any.whl | grep tests
# Should return nothing
```

### 6. Test on TestPyPI

**Configure TestPyPI repository** (first time only):

```bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
```

**Publish to TestPyPI**:

```bash
poetry publish -r testpypi
```

You'll be prompted for credentials. Use your TestPyPI API token (see "Setting Up API Tokens" below).

**Verify TestPyPI package page**:

Visit https://test.pypi.org/project/agentic-prompt-manager/ and verify:
- Version number is correct
- README renders properly
- Metadata is complete
- Download files are available

### 7. Test Installation from TestPyPI

Create a fresh virtual environment and test installation:

```bash
# Create fresh environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from TestPyPI (with fallback to PyPI for dependencies)
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            agentic-prompt-manager

# Test basic functionality
python -c "import prompt_manager; print(prompt_manager.__version__)"

# Test importing integrations
python -c "from prompt_manager.integrations import BaseIntegration"

# Install with extras
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            'agentic-prompt-manager[openai]'

# Run an example
cd examples/integrations/
python openai_example.py

# Cleanup
deactivate
rm -rf test-env
```

If any issues are found, fix them and repeat from step 4.

### 8. Create Git Tag

Once TestPyPI testing is successful, create a release tag:

```bash
# Create annotated tag
git tag -a vX.Y.Z -m "Release version X.Y.Z"

# Verify tag
git tag -l vX.Y.Z
git show vX.Y.Z

# Push tag to GitHub
git push origin vX.Y.Z
```

### 9. Publish to PyPI

**IMPORTANT**: This step is irreversible. Ensure TestPyPI testing was successful.

```bash
# Publish to production PyPI
poetry publish

# Enter your PyPI API token when prompted
```

### 10. Verify PyPI Publication

Check the PyPI package page:

Visit https://pypi.org/project/agentic-prompt-manager/ and verify:
- Version X.Y.Z is listed as latest
- README renders correctly
- All classifiers are correct
- Download files are available
- Documentation links work

### 11. Test Installation from PyPI

```bash
# Create fresh environment
python -m venv verify-env
source verify-env/bin/activate

# Install from PyPI
pip install agentic-prompt-manager

# Verify version
python -c "import prompt_manager; print(prompt_manager.__version__)"

# Test with extras
pip install 'agentic-prompt-manager[all]'

# Cleanup
deactivate
rm -rf verify-env
```

### 12. Create GitHub Release

1. Go to https://github.com/yourusername/prompt-manager/releases
2. Click "Draft a new release"
3. Select the tag `vX.Y.Z` created earlier
4. Set release title: `vX.Y.Z - [Brief Description]`
5. Copy changelog entry for this version to release notes
6. Add highlights and notable changes
7. Attach the wheel and sdist files from `dist/`
8. Check "Set as the latest release"
9. Click "Publish release"

### 13. Post-Release Verification

Monitor for issues:

- [ ] GitHub Actions workflows completed successfully
- [ ] PyPI download stats are tracking (may take a few hours)
- [ ] No immediate bug reports or installation issues
- [ ] Documentation is accessible
- [ ] Examples work for new installations

### 14. Announce Release

Share the release with the community:

- [ ] Update project website (if applicable)
- [ ] Post announcement on project blog
- [ ] Share on social media (Twitter, LinkedIn)
- [ ] Post in relevant communities (r/Python, Python Discord, etc.)
- [ ] Notify users of breaking changes (if major version)

## Rollback Procedures

### If Critical Bug Found After Release

**Option 1: Yank the Release (Recommended)**

```bash
# Hide the broken version from pip install (but don't delete)
# Users who already installed can continue using it
poetry publish --yank vX.Y.Z --reason "Critical bug: [description]"
```

**Option 2: Immediate Patch Release**

1. Fix the critical bug
2. Bump to X.Y.Z+1
3. Run through release process (abbreviated):
   - Update version numbers
   - Update CHANGELOG
   - Build and test on TestPyPI
   - Publish to PyPI
4. Create GitHub release with fix notes

### If TestPyPI Testing Reveals Issues

Simply fix the issues and rebuild:

```bash
# Fix the code
# Update version if needed (e.g., alpha.1 -> alpha.2)
rm -rf dist/
poetry build
poetry publish -r testpypi
```

TestPyPI allows multiple uploads of pre-release versions.

## Setting Up API Tokens

### PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Set scope to "Entire account" or "Project: prompt-manager"
4. Copy the token (starts with `pypi-`)
5. Configure Poetry:

```bash
poetry config pypi-token.pypi <your-token>
```

### TestPyPI API Token

1. Go to https://test.pypi.org/manage/account/token/
2. Create a new API token
3. Copy the token
4. Configure Poetry:

```bash
poetry config pypi-token.testpypi <your-token>
```

### GitHub Actions Secrets

For automated releases via GitHub Actions:

1. **PyPI Token**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token with scope "Project: agentic-prompt-manager" (or "Entire account")
   - Copy the token (starts with `pypi-`)
   - Go to GitHub repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_TOKEN`
   - Value: paste the PyPI token
   - Click "Add secret"

2. **TestPyPI Token**:
   - Go to https://test.pypi.org/manage/account/token/
   - Create a new API token
   - Copy the token
   - In GitHub repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `TEST_PYPI_TOKEN`
   - Value: paste the TestPyPI token
   - Click "Add secret"

3. **Codecov Token** (optional, for coverage uploads):
   - Go to https://codecov.io/ and sign in with GitHub
   - Add the repository
   - Copy the upload token
   - In GitHub repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: paste the Codecov token
   - Click "Add secret"

**IMPORTANT**: These secrets must be configured before GitHub Actions workflows can publish to PyPI/TestPyPI. The workflows will fail if the secrets are missing.

## Automated Release (GitHub Actions)

Once configured, releases can be automated:

1. Create and push a tag:
   ```bash
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   git push origin vX.Y.Z
   ```

2. GitHub Actions will automatically:
   - Run all tests
   - Build the package
   - Publish to PyPI (on release tags)
   - Create GitHub release

3. Monitor the Actions tab for workflow status

## Version Management Tips

### Development Workflow

```bash
# Main branch: stable releases only
git checkout main

# Feature development
git checkout -b feature/new-feature
# ... make changes ...
git commit -m "feat: add new feature"

# After PR merge, bump version for release
git checkout main
git pull
# Update version in __init__.py and pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
```

### Pre-release Versions

For alpha/beta releases:

```bash
# Set version to "0.2.0-alpha.1"
# Build and publish to TestPyPI only
poetry build
poetry publish -r testpypi

# Later, for beta:
# Set version to "0.2.0-beta.1"
# Repeat process

# Final release:
# Set version to "0.2.0"
# Publish to PyPI
```

## Troubleshooting

### "Version already exists on PyPI"

PyPI doesn't allow re-uploading the same version. You must bump the version number.

### "File already exists"

Clear the dist directory:
```bash
rm -rf dist/
poetry build
```

### "Authentication failed"

Re-configure your API token:
```bash
poetry config pypi-token.pypi <your-token>
```

### "Package is too large"

Check what's being included:
```bash
unzip -l dist/*.whl
```

Update `tool.poetry.exclude` in `pyproject.toml` to exclude unnecessary files.

## Release Checklist Template

Copy this checklist for each release:

```markdown
## Release vX.Y.Z Checklist

### Pre-Release
- [ ] All tests passing
- [ ] Coverage >= 90%
- [ ] Type checking passes
- [ ] Security scans pass
- [ ] Version bumped
- [ ] CHANGELOG updated
- [ ] Examples tested

### Testing
- [ ] Built locally
- [ ] Package contents inspected
- [ ] Published to TestPyPI
- [ ] Installed from TestPyPI
- [ ] Functionality verified

### Release
- [ ] Git tag created
- [ ] Published to PyPI
- [ ] PyPI page verified
- [ ] Installed from PyPI
- [ ] GitHub release created

### Post-Release
- [ ] GitHub Actions successful
- [ ] Announcement posted
- [ ] Documentation updated
- [ ] Monitoring for issues
```

---

**Last Updated**: 2025-01-19
**Next Review**: Before each release
