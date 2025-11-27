# Prompt Manager - Changes Summary

This document tracks all changes made during the debugging/update session on 2025-11-26.

## Critical API Changes

### 1. Manager Initialization
```python
# OLD (WRONG)
pm = PromptManager(prompts_dir="prompts")

# NEW (CORRECT)
pm = PromptManager.create(prompt_dir="prompts")
```

### 2. Getting Prompts
```python
# OLD (WRONG)
template = pm.get_template("greeting")
result = template.render(variables)

# NEW (CORRECT)
prompt = pm.get_prompt("greeting")
result = prompt.render(variables)
```

### 3. Prompt Rendering
```python
# Both methods now work:
result = prompt.render(variables)  # NEW: Direct rendering on Prompt
result = pm.render("greeting", variables)  # Manager rendering
```

## Template Engine: Handlebars NOT Jinja2

### What Changed
The system uses **Handlebars (pybars4)**, NOT Jinja2 as documented in the old tutorial.

### Syntax Differences

| Feature | Jinja2 (WRONG) | Handlebars (CORRECT) |
|---------|----------------|----------------------|
| Variables | `{{ name }}` | `{{ name }}` ✓ |
| If statement | `{% if x %}...{% endif %}` | `{{#if x}}...{{/if}}` ✓ |
| For loop | `{% for item in items %}` | `{{#each items}}...{{/each}}` ✓ |
| Filters | `{{ name \| title }}` | ❌ NOT SUPPORTED |
| Filters | `{{ tags \| join(", ") }}` | ❌ NOT SUPPORTED |

### How to Handle Formatting

**DON'T** try to use Jinja2 filters:
```python
# This WON'T work
template = "{{ name | title }}"
```

**DO** pre-process data in Python:
```python
# This WORKS
raw_data = {"name": "john doe"}
formatted_data = {"name": raw_data["name"].title()}
result = prompt.render(formatted_data)
```

## Prompt Template Changes

### greeting.yaml
```yaml
# Variables changed
variables:
  - name
  - role      # Changed from 'service'
```

Usage:
```python
prompt.render({"name": "Alice", "role": "Developer"})
```

### data_analysis.yaml
```yaml
# Completely restructured
variables:
  - datasets       # List of {name, rows} dicts
  - analysis_type  # String: "trend", "correlation", etc.
```

Usage:
```python
prompt.render({
    "datasets": [
        {"name": "sales_2024", "rows": 10000},
        {"name": "customers", "rows": 5000}
    ],
    "analysis_type": "trend"
})
```

### code_review.yaml
```yaml
# focus_areas is now a list
variables:
  - language
  - code
  - focus_areas  # List of strings
```

Usage:
```python
prompt.render({
    "language": "python",
    "code": "def hello(): return 'world'",
    "focus_areas": ["security", "performance"]
})
```

## Schema Validation Updates

### List Types
List types now require `item_type`:
```yaml
- name: "focus_areas"
  type: "list"
  item_type: "string"  # REQUIRED for lists
  default: []
```

### Auto-Loading
Schemas are automatically loaded when referenced by prompts:
```python
# Schemas auto-load - no manual loading needed
pm = PromptManager.create(prompt_dir="prompts")
# code_review_input, data_analysis_input, etc. are already loaded
```

## Prompt.render() Enhancements

The `prompt.render()` method now has full features:

```python
result = prompt.render(
    variables,
    validate_input=True,    # Validates against input_schema
    inject_schemas=True,    # Injects output_schema descriptions
    schema_loader=None      # Optional custom loader
)
```

Features:
- ✅ Input validation (if input_schema defined)
- ✅ Output schema injection (if output_schema defined)
- ✅ Schema loader auto-injected from PromptManager
- ❌ No caching (use pm.render() for caching)
- ❌ No metrics (use pm.render() for metrics)

## Files That Need Updating

### Tutorial Notebook
- [ ] Replace all "Jinja2" references with "Handlebars"
- [ ] Remove filter examples (title, join, upper, round)
- [ ] Update all code examples to use correct API
- [ ] Add section on pre-processing data instead of filters
- [ ] Update variable names in examples to match YAML files

### Steering Documents (.claude/steering/)
- [ ] product.md - Update template engine references
- [ ] tech.md - Update to Handlebars, remove Jinja2
- [ ] structure.md - Verify API examples are correct
- [ ] RECOMMENDATIONS.md - Update any template examples

### Spec Documents (.claude/specs/)
- [ ] Check dual-sync-async-interface/ - Remove if async was removed
- [ ] Verify all specs use correct API

## Migration Guide for Users

### From Old API to New API

**Step 1: Update Initialization**
```python
# Before
pm = PromptManager(prompts_dir="./prompts")

# After
pm = PromptManager.create(prompt_dir="./prompts")
```

**Step 2: Update Template Access**
```python
# Before
template = pm.get_template("greeting")

# After
prompt = pm.get_prompt("greeting")
```

**Step 3: Update Rendering**
```python
# Both work now (choose based on needs)
result = prompt.render(variables)      # Simple rendering
result = pm.render("greeting", variables)  # With caching/metrics
```

**Step 4: Update Template Syntax**
```python
# Before (Jinja2 filters)
template = "{{ name | title }}"
data = {"name": "john doe"}

# After (pre-process)
template = "{{ name }}"
data = {"name": "john doe".title()}
```

## Testing Your Updates

Run this to verify everything works:

```python
from prompt_manager import PromptManager

# Test initialization
pm = PromptManager.create(prompt_dir="examples/prompts")

# Test greeting
prompt = pm.get_prompt("greeting")
result = prompt.render({"name": "Alice", "role": "Developer"})
assert "Alice" in result
assert "Developer" in result

# Test data_analysis with lists
prompt = pm.get_prompt("data_analysis")
result = prompt.render({
    "datasets": [{"name": "test", "rows": 100}],
    "analysis_type": "trend"
})
assert "test" in result

# Test code_review with list validation
prompt = pm.get_prompt("code_review")
result = prompt.render({
    "language": "python",
    "code": "def test(): pass",
    "focus_areas": ["security"]
})
assert "security" in result

print("✓ All tests passed!")
```

## Summary

**What Works:**
- ✅ PromptManager.create() API
- ✅ prompt.render() with full validation
- ✅ Handlebars templates ({{variables}}, {{#if}}, {{#each}})
- ✅ Schema auto-loading
- ✅ List types in schemas

**What Doesn't Work:**
- ❌ PromptManager(prompts_dir=...)
- ❌ get_template()
- ❌ Jinja2 filters (| title, | join, etc.)
- ❌ Jinja2 syntax ({% %})

**Best Practices:**
1. Always use `PromptManager.create()`
2. Use `prompt.render()` for simplicity
3. Pre-process data in Python instead of template filters
4. Let schemas auto-load (don't load manually)
5. Use Handlebars syntax for templates
