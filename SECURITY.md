# Security Policy

## Supported Versions

The following versions of Prompt Manager are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by emailing the maintainers. Include:

- **Description of the vulnerability**: Clear explanation of the security issue
- **Steps to reproduce**: Detailed steps to reproduce the vulnerability
- **Potential impact**: Assessment of the severity and potential consequences
- **Suggested fix** (if any): Proposed solution or mitigation

### Response Timeline

- **Initial Response**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Investigation**: We will investigate and validate the reported vulnerability
- **Resolution**: We will work on a fix and coordinate disclosure timing with you
- **Disclosure**: We will publicly disclose the vulnerability after a fix is available

## Security Best Practices

### API Key Management

**Never commit API keys to the repository.**

Use environment variables to manage API keys and secrets:

```python
import os

# Load API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# Use with framework integration
client = openai.AsyncOpenAI(api_key=api_key)
```

### Environment Files

Use `.env` files for local development (excluded from git):

```bash
# .env (never commit this file!)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

```python
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Now environment variables are available
api_key = os.getenv("OPENAI_API_KEY")
```

### Sensitive Data in Prompts

- **Do not include** hardcoded API keys, passwords, or secrets in prompt templates
- **Do not include** personally identifiable information (PII) in prompt YAML files
- **Do validate** all user inputs before rendering prompts
- **Do sanitize** user-provided variables to prevent injection attacks

### Dependency Security

We take dependency security seriously:

- **Automated Scanning**: Dependencies are scanned weekly with `safety` and `bandit`
- **Security Updates**: Security issues are addressed within 48 hours
- **Critical Issues**: Critical vulnerabilities trigger immediate patch releases
- **Dependabot**: Automated dependency update PRs are reviewed promptly

### Secure Coding Practices

- **Input Validation**: All user inputs are validated before processing
- **Type Safety**: Pydantic v2 models provide runtime validation
- **Error Handling**: Exceptions are caught and wrapped in package exceptions
- **Async Safety**: All async operations use proper context management

## Security Features

### Built-in Protections

1. **Schema Validation**: Input and output schemas prevent malformed data
2. **Type Checking**: Mypy strict mode catches type errors at development time
3. **Pydantic Validation**: Runtime validation of all data models
4. **Structured Logging**: Security events are logged for audit trails

### Recommended Practices

1. **Use virtual environments** to isolate dependencies
2. **Pin dependency versions** in production deployments
3. **Regular updates** to get latest security patches
4. **Security scanning** in CI/CD pipelines
5. **Principle of least privilege** for API keys and credentials

## Known Security Considerations

### Template Injection

Handlebars templates are rendered with user-provided variables. To prevent template injection:

- **Validate variables** before rendering
- **Use schema validation** to ensure expected data types
- **Sanitize user input** if accepting untrusted data
- **Limit template complexity** to reduce attack surface

### LLM-Specific Risks

When integrating with LLM APIs:

- **Prompt injection**: User inputs could manipulate prompt behavior
- **Data exposure**: Sensitive data in prompts is sent to external APIs
- **Rate limiting**: Implement rate limits to prevent abuse
- **Cost control**: Monitor API usage to prevent unexpected costs

## Security Audit History

No security audits have been performed yet. This section will be updated with audit results.

## Acknowledgments

We appreciate the security research community and will acknowledge researchers who responsibly disclose vulnerabilities (with permission).

---

**Last Updated**: 2025-01-19
