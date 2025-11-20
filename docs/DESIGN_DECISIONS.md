# Design Decisions

This document explains key design decisions and their rationale.

## 1. Python 3.11+ Requirement

**Decision:** Require Python 3.11 or higher

**Rationale:**
- **Performance**: 10-60% faster than Python 3.10
- **Better error messages**: More helpful tracebacks
- **Type hints**: Enhanced type system features
- **Exception groups**: Better async error handling
- **TOML support**: Built-in tomllib

**Trade-offs:**
- Smaller user base (3.11 adoption growing)
- Can't use on older systems without upgrade

## 2. Pydantic v2 for Models

**Decision:** Use Pydantic v2 for all data models

**Rationale:**
- **Performance**: 5-50x faster than v1
- **Type safety**: Better mypy integration
- **Validation**: Runtime validation with clear errors
- **Serialization**: Built-in JSON/dict serialization
- **Documentation**: Auto-generated schemas

**Trade-offs:**
- Breaking changes from v1
- Different API from v1 projects

**Code Example:**
```python
class Prompt(BaseModel):
    model_config = ConfigDict(
        frozen=False,
        extra="forbid",
        validate_assignment=True,
    )
    id: str = Field(..., min_length=1)
```

## 3. Protocol-Based Design

**Decision:** Use Protocols instead of ABC inheritance

**Rationale:**
- **Structural typing**: Duck typing with type safety
- **No coupling**: Third-party implementations don't need inheritance
- **Flexibility**: Can implement protocol retroactively
- **Testability**: Easy to create test doubles

**Trade-offs:**
- Less obvious relationship than inheritance
- Need @runtime_checkable for isinstance checks

**Code Example:**
```python
@runtime_checkable
class StorageBackendProtocol(Protocol):
    async def save(self, prompt: Prompt) -> None: ...
    async def load(self, prompt_id: str) -> Prompt: ...
```

## 4. Async/Await Throughout

**Decision:** Make all I/O operations async

**Rationale:**
- **Performance**: Non-blocking I/O
- **Scalability**: Handle many concurrent operations
- **Modern**: Aligns with async Python ecosystem
- **Composability**: Easy to integrate with async frameworks

**Trade-offs:**
- More complex than sync code
- Async context required (asyncio.run)
- Learning curve for async patterns

**Code Example:**
```python
async def render(self, prompt_id: str, variables: Mapping[str, Any]) -> str:
    prompt = await self._registry.get(prompt_id)
    result = await self._template_engine.render(...)
    return result
```

## 5. Handlebars for Templating

**Decision:** Use Handlebars (pybars4) instead of Jinja2

**Rationale:**
- **Logic-less**: Enforces separation of concerns
- **Familiar**: Common in JavaScript ecosystems
- **Safe**: Less risk of code injection
- **Portable**: Templates work across languages

**Trade-offs:**
- Less powerful than Jinja2
- Smaller Python community
- Limited helper ecosystem

**Alternatives Considered:**
- **Jinja2**: Too powerful, encourages logic in templates
- **Mustache**: Less features than Handlebars
- **f-strings**: No template reuse/validation

## 6. Semantic Versioning

**Decision:** Enforce semantic versioning (X.Y.Z)

**Rationale:**
- **Standard**: Industry-wide convention
- **Clarity**: Clear meaning (major.minor.patch)
- **Tooling**: Many tools support semver
- **Compatibility**: Easy to reason about changes

**Trade-offs:**
- More rigid than free-form versions
- Need to choose version bump level

**Code Example:**
```python
@field_validator("version")
@classmethod
def validate_semver(cls, v: str) -> str:
    parts = v.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError("Version must be in semver format")
    return v
```

## 7. Observer Pattern for Hooks

**Decision:** Use observer pattern for lifecycle hooks

**Rationale:**
- **Decoupling**: Core logic independent of observers
- **Extensibility**: Add observers without modification
- **Multiple observers**: Many observers simultaneously
- **Testability**: Easy to test with/without observers

**Trade-offs:**
- Indirect flow (harder to trace)
- Performance overhead per observer
- No return values from observers

**Code Example:**
```python
for observer in self._observers:
    await observer.on_render_complete(prompt_id, version, execution)
```

## 8. File System Storage Default

**Decision:** Provide file system storage as default persistence

**Rationale:**
- **Simple**: No database setup required
- **Portable**: Works everywhere
- **Debuggable**: Files are human-readable JSON
- **Version control**: Can commit to git

**Trade-offs:**
- Slower than database for large datasets
- No transactions
- Limited query capabilities
- Concurrent write issues

**Future:**
- PostgreSQL backend for production
- Redis backend for caching
- S3 backend for cloud deployments

## 9. Structured Logging with structlog

**Decision:** Use structlog instead of standard logging

**Rationale:**
- **Structured**: Machine-parseable logs
- **Context**: Easy to add context to all logs
- **Performance**: Lazy evaluation
- **Integration**: Works with OpenTelemetry

**Trade-offs:**
- Different API from standard logging
- Additional dependency
- Learning curve

**Code Example:**
```python
logger.info(
    "prompt_rendered",
    prompt_id=prompt_id,
    version=version,
    duration_ms=duration,
)
```

## 10. In-Memory Metrics

**Decision:** Collect metrics in-memory by default

**Rationale:**
- **Simple**: No external dependencies
- **Fast**: No network overhead
- **Self-contained**: Works without setup
- **Development**: Easy for development/testing

**Trade-offs:**
- Lost on restart
- Single process only
- Memory usage grows
- No historical analysis

**Future:**
- Prometheus exporter
- StatsD integration
- Time-series database

## 11. Optional Dependencies

**Decision:** Make plugin dependencies optional

**Rationale:**
- **Lean core**: Don't force unused dependencies
- **Flexibility**: Install only what you need
- **Fast install**: Smaller package
- **Version conflicts**: Avoid dependency hell

**Trade-offs:**
- More complex installation
- Need to document extras
- Import errors if not installed

**Code Example:**
```toml
[tool.poetry.extras]
openai = ["openai"]
anthropic = ["anthropic"]
all = ["openai", "anthropic", "langchain-core"]
```

## 12. Frozen Models for Immutability

**Decision:** Use frozen=True for immutable models

**Rationale:**
- **Thread safety**: No concurrent modification
- **Predictability**: Can't change unexpectedly
- **Cacheable**: Safe to cache instances
- **Debugging**: Easier to reason about

**Trade-offs:**
- Need to create new instances for changes
- More memory (can't reuse)
- Less convenient for mutations

**Code Example:**
```python
class Message(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
```

## 13. Type Safety with Mypy Strict Mode

**Decision:** Enforce mypy strict mode

**Rationale:**
- **Correctness**: Catch bugs at type-check time
- **Documentation**: Types document expected inputs
- **Refactoring**: Safe to refactor with types
- **IDE support**: Better autocomplete/hints

**Trade-offs:**
- More verbose code
- Learning curve for type system
- Slower development initially

**Configuration:**
```toml
[tool.mypy]
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
```

## 14. Separate Registry and Storage

**Decision:** Separate in-memory registry from persistent storage

**Rationale:**
- **Performance**: Fast registry access
- **Flexibility**: Swap storage backends
- **Caching**: Registry acts as cache
- **Separation**: Clear responsibilities

**Trade-offs:**
- Two places to manage
- Synchronization complexity
- More memory usage

**Architecture:**
```
Registry (in-memory, fast) ←→ Storage (persistent, slower)
```

## 15. Version Store Separate from Registry

**Decision:** Separate version history from prompt registry

**Rationale:**
- **Concerns**: Different use cases
- **Performance**: Don't load history unless needed
- **Storage**: Different storage requirements
- **Optional**: Can disable versioning

**Trade-offs:**
- More components to manage
- Potential inconsistencies
- More complex initialization

## 16. Exception Hierarchy

**Decision:** Create comprehensive exception hierarchy

**Rationale:**
- **Specific handling**: Catch specific errors
- **Context**: Exceptions carry context
- **Documentation**: Clear error types
- **Debugging**: Better error messages

**Trade-offs:**
- Many exception classes
- Need to choose right exception
- More code to maintain

**Hierarchy:**
```
PromptManagerError
├── PromptError
├── TemplateError
├── VersionError
├── StorageError
└── PluginError
```

## 17. Chat vs Text Format Separation

**Decision:** Separate template types for chat and text

**Rationale:**
- **Type safety**: Different fields for different formats
- **Validation**: Format-specific validation
- **Clarity**: Clear which format is used
- **Plugins**: Easy for plugins to handle

**Trade-offs:**
- Two template types to manage
- Conversion complexity
- More model code

## 18. Builder Pattern Not Used

**Decision:** Use direct model instantiation instead of builders

**Rationale:**
- **Pydantic**: Models are already easy to create
- **Validation**: Pydantic validates on creation
- **Simple**: Less code to maintain
- **Standard**: Follows Python conventions

**Alternatives Considered:**
- Builder pattern: Too verbose
- Factory functions: Not needed with Pydantic

## 19. No CLI in Core Package

**Decision:** No CLI tool in initial release

**Rationale:**
- **Focus**: Library-first approach
- **Flexibility**: Users build their own CLI
- **Simplicity**: Smaller core package
- **Future**: Can add later as separate package

**Future:**
- Separate CLI package
- REST API server
- Web UI

## 20. YAML Over TOML/JSON

**Decision:** Use YAML for prompt schemas

**Rationale:**
- **Readability**: Most readable for prompts
- **Comments**: Supports comments
- **Multiline**: Easy multiline strings
- **Common**: Used in many systems

**Trade-offs:**
- Indentation-sensitive
- More complex parser
- Security concerns (unsafe loading)

**Safety:**
```python
yaml.safe_load(content)  # Always use safe_load
```

## Lessons for Future Development

1. **Start simple**: Add complexity only when needed
2. **Type everything**: Strict typing catches bugs early
3. **Protocol over inheritance**: More flexible
4. **Async by default**: Easier to add sync wrapper than vice versa
5. **Separate concerns**: Clear boundaries between components
6. **Optional features**: Keep core lean
7. **Test extensively**: High coverage with property tests
8. **Document decisions**: Future maintainers will thank you
