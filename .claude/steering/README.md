# Steering Documentation

This directory contains comprehensive steering documents for the Prompt Manager project. These documents guide all development work, ensuring consistency and alignment with project goals.

## Document Overview

### 1. [product.md](./product.md)
**Product vision, features, and use cases**

Essential reading for understanding:
- What the product is and who it's for
- Core value propositions
- Key features and capabilities
- Common use cases and integration patterns
- Product roadmap and future plans

Use this when:
- Planning new features
- Writing documentation
- Making product decisions
- Communicating with stakeholders

### 2. [tech.md](./tech.md)
**Technology stack and development guidelines**

Comprehensive guide covering:
- Core technology stack (Python 3.11+, Pydantic v2, etc.)
- Development patterns (async/await, protocols, dependency injection)
- Type safety with mypy strict mode
- Code style guidelines
- Testing patterns
- Performance guidelines
- Security best practices

Use this when:
- Implementing new features
- Setting up development environment
- Reviewing code
- Making architectural decisions

### 3. [structure.md](./structure.md)
**Project structure and organization**

Detailed documentation of:
- Directory layout and file organization
- Module organization and responsibilities
- Import conventions
- File naming conventions
- Configuration files
- Test organization
- When to create new modules

Use this when:
- Adding new modules or features
- Refactoring code
- Navigating the codebase
- Understanding component relationships

### 4. [python-best-practices.md](./python-best-practices.md)
**Python-specific patterns and conventions**

In-depth Python guidance including:
- Python 3.11+ requirements and features
- Async/await patterns
- Type hints and type safety
- Pydantic best practices
- Error handling patterns
- Code organization
- Performance patterns
- Testing patterns
- Logging best practices
- Security best practices
- Common antipatterns to avoid

Use this when:
- Writing Python code
- Doing code reviews
- Solving common problems
- Learning project patterns

## Quick Reference

### For New Features

1. **Start with product.md**: Understand if the feature aligns with product vision
2. **Check tech.md**: Identify relevant patterns and technologies
3. **Review structure.md**: Determine where code should live
4. **Apply python-best-practices.md**: Write code following established patterns

### For Code Reviews

1. **Check tech.md**: Verify patterns are followed
2. **Verify structure.md**: Ensure code is in right place
3. **Apply python-best-practices.md**: Check for antipatterns

### For New Contributors

Read in this order:
1. product.md - Understand the product
2. structure.md - Navigate the codebase
3. tech.md - Learn development patterns
4. python-best-practices.md - Master implementation details

## Integration with Spec-Driven Development

These steering documents work with the spec-driven development workflow:

### Phase 1: Planning (spec-product-manager)
- Uses **product.md** for product alignment
- References **tech.md** for technical feasibility
- Applies **structure.md** for architecture decisions

### Phase 2: Implementation (spec-execution-agent)
- Follows **tech.md** for implementation patterns
- Uses **structure.md** for file organization
- Applies **python-best-practices.md** for code quality

### Phase 3: Quality Assurance
- Validates against **tech.md** guidelines
- Checks **python-best-practices.md** compliance
- Ensures **structure.md** organization

## Document Maintenance

### When to Update

Update these documents when:
- Adding major features or technologies
- Changing architectural patterns
- Discovering new best practices
- Resolving significant technical debt
- Receiving feedback from contributors

### Update Process

1. Make changes to relevant document(s)
2. Update this README if structure changes
3. Announce changes to team
4. Update related examples and tests

### Version History

- **2024-11-19**: Initial creation
  - Created product.md with vision and roadmap
  - Created tech.md with stack and patterns
  - Created structure.md with organization
  - Created python-best-practices.md with Python patterns

## Related Documentation

### Project Root Documentation

- **README.md**: Quick start and overview
- **ARCHITECTURE.md**: Detailed architecture documentation
- **DESIGN_DECISIONS.md**: Rationale for key decisions
- **PACKAGE_SUMMARY.md**: Package overview
- **QUICK_START.md**: Getting started guide
- **RECOMMENDATIONS.md**: Best practices and recommendations

### Specs Directory

- **.claude/specs/**: Feature specifications
- **.claude/specs/security-requirements/**: Security documentation

### Examples

- **examples/**: Usage examples and patterns

## Contributing to Steering Docs

### Style Guidelines

- Use clear, concise language
- Include code examples for patterns
- Explain the "why" not just the "what"
- Keep examples realistic and practical
- Use consistent formatting

### Structure Guidelines

- Start with overview/introduction
- Use clear hierarchical headings
- Include quick reference sections
- Provide cross-references to related docs
- End with actionable takeaways

## Questions?

If you have questions about:
- **Product direction**: See product.md or ask product manager
- **Technical approach**: See tech.md or ask tech lead
- **Code location**: See structure.md or ask in code review
- **Python patterns**: See python-best-practices.md or ask in code review

---

**Maintained by**: Project team
**Last Updated**: 2024-11-19
**Next Review**: Quarterly or after major changes
