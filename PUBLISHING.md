# Publishing to PyPI

Quick guide for publishing `agentic-prompt-manager` to PyPI.

## Setup (One-Time)

### 1. Get Your PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Set scope to "Project: agentic-prompt-manager" (or "Entire account")
4. Copy the token (starts with `pypi-`)

### 2. Configure Environment

Add your token to `.env`:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your token
# The file is already ignored by git
```

Your `.env` should look like:
```bash
TWINE_USERNAME=__token__
TWINE_PASSWORD=pypi-YOUR_ACTUAL_TOKEN_HERE
```

## Publishing

### Option 1: Using Twine with .env

```bash
# Install twine
pip install twine

# Load environment variables and publish
source <(grep -v '^#' .env | xargs -I {} echo export {})
twine upload dist/*
```

### Option 2: Using Poetry

```bash
# Configure token with Poetry
poetry config pypi-token.pypi pypi-YOUR_TOKEN_HERE

# Build and publish
poetry build
poetry publish
```

### Option 3: Using GitHub Actions (Recommended)

The repository is configured with GitHub Actions for automated publishing:

1. Set up PyPI Trusted Publisher (see main README)
2. Push a tag: `git tag -a v0.1.0 -m "Release v0.1.0" && git push origin v0.1.0`
3. GitHub Actions will automatically build and publish

## Testing on TestPyPI

Before publishing to production PyPI, test on TestPyPI:

### 1. Get TestPyPI Token

1. Go to https://test.pypi.org/manage/account/token/
2. Create a token
3. Add to `.env`:

```bash
TWINE_USERNAME=__token__
TWINE_PASSWORD=pypi-YOUR_TEST_PYPI_TOKEN_HERE
TWINE_REPOSITORY_URL=https://test.pypi.org/legacy/
```

### 2. Publish to TestPyPI

```bash
# Build the package
poetry build

# Upload to TestPyPI
source <(grep -v '^#' .env | xargs -I {} echo export {})
twine upload dist/*
```

### 3. Test Installation

```bash
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            agentic-prompt-manager
```

## Security Notes

- ✓ `.env` is in `.gitignore` - will NOT be committed
- ✓ `.env` is excluded from package builds
- ✓ Never share your API tokens
- ✓ Tokens can be revoked at https://pypi.org/manage/account/token/

## Troubleshooting

### "Invalid or non-existent authentication"

- Check your token is correct in `.env`
- Ensure token scope includes the project
- Verify `TWINE_USERNAME=__token__` (literal text, not a placeholder)

### "File already exists"

PyPI doesn't allow re-uploading the same version. Bump the version in `pyproject.toml` first.

### Environment variables not loading

```bash
# Verify .env is set correctly
cat .env

# Manually export if needed
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE
twine upload dist/*
```
