# Jupyter Notebook Corrections Guide

## Issues Found

### 1. YAML Structure References (INCORRECT)
The notebook says:
```yaml
name: greeting           # WRONG - actual field is "id"
version: 1.0.0
description: A greeting  # WRONG - actual location is "metadata.description"
template: |
  Hello {{ name }}
```

**Actual YAML structure:**
```yaml
id: greeting                           # "id" not "name"
version: 1.0.0
uid: e3960aca-bfe7-4c16-a3c6-68f4f5e757af
format: text                           # NEW: format specification
template:
  content: Hello {{name}}!             # Nested under "template.content"
  variables:
    - name
    - role
  partials: {}
  helpers: {}
chat_template: null
status: active
created_at: '2025-11-26T22:42:52'
updated_at: '2025-11-26T22:42:52'
metadata:                              # "description" is here
  author: System
  description: Simple greeting prompt  # Under metadata, not root
  tags:
    - greeting
  category: general
  use_cases: []
  model_recommendations: []
  temperature: null
  max_tokens: null
  custom: {}
input_schema: null
output_schema: null
```

### 2. Jinja2 References (ALL INCORRECT)
Throughout the notebook:
- "Jinja2 syntax" → Should be "Handlebars syntax"
- "{% if %}" → Should be "{{#if}}"
- "{% for %}" → Should be "{{#each}}"
- Filter examples (| title, | join, | upper) → Should show Python pre-processing

### 3. Filter Examples (NEED COMPLETE REWRITE)

**Current (WRONG):**
```python
template = """
Name: {{ name | title }}
Tags: {{ tags | join(", ") | upper }}
Score: {{ score | round(2) }}
"""
```

**Corrected:**
```python
# Pre-process data in Python
raw_data = {
    "name": "john doe",
    "tags": ["python", "ai", "data"],
    "score": 3.14159
}

# Apply formatting in Python
formatted_data = {
    "name": raw_data["name"].title(),           # Title case
    "tags": ", ".join(raw_data["tags"]).upper(), # Join and uppercase
    "score": f"{raw_data['score']:.2f}"         # Round to 2 decimals
}

# Use simple Handlebars template
template = """
Name: {{name}}
Tags: {{tags}}
Score: {{score}}
"""

# Render with formatted data
prompt = Prompt(
    id="demo",
    version="1.0.0",
    format=PromptFormat.TEXT,
    template=PromptTemplate(
        content=template,
        variables=["name", "tags", "score"]
    )
)
result = prompt.render(formatted_data)
```

## Section-by-Section Corrections

### Cell 1 - Introduction
**Issues:**
- Line: "Use advanced template features (conditionals, loops, filters)"
  - Remove "filters" or clarify "pre-process data for formatting"
- Line: "Template Engine: Dynamic variable substitution with Jinja2"
  - Change to: "Template Engine: Dynamic variable substitution with Handlebars (pybars4)"

### Section 2 - Template Engine Features
**Complete rewrite needed:**

**OLD heading:** "Understanding Jinja2 Templates"
**NEW heading:** "Understanding Handlebars Templates"

**OLD text:**
"Prompt Manager uses Jinja2, a powerful template engine..."

**NEW text:**
"Prompt Manager uses Handlebars (via pybars4), a logic-less template engine..."

**Features table:**
| Feature | Handlebars Syntax |
|---------|-------------------|
| Variables | `{{variable_name}}` |
| Conditionals | `{{#if condition}}...{{/if}}` |
| Loops | `{{#each list}}...{{/each}}` |
| Nested access | `{{user.name}}` |
| Comments | `{{! comment }}` |

**Add new section:** "Why No Filters?"
```markdown
Handlebars is "logic-less" by design - it doesn't include built-in filters like Jinja2.
This is actually a **best practice**:
- Keep templates simple and readable
- Put formatting logic in testable Python code
- Easier to maintain and debug

Example:
```python
# Good: Format in Python
data = {
    "name": user.name.title(),
    "count": f"{count:,}"  # Add commas
}
result = prompt.render(data)

# Bad: Try to use non-existent filters
template = "{{name | title}}"  # Won't work!
```
```

### Section on Filters (DELETE AND REPLACE)
**Delete these sections:**
- "Filters for Text Transformation"
- Examples using | upper, | title, | join, | round

**Replace with:** "Data Formatting with Python"

```markdown
### Data Formatting with Python

Since Handlebars doesn't have filters, pre-process your data in Python:

#### String Formatting
```python
raw = {"name": "john doe", "company": "acme corp"}

formatted = {
    "name": raw["name"].title(),          # John Doe
    "company": raw["company"].upper(),    # ACME CORP
    "initials": "".join(w[0] for w in raw["name"].split()).upper()  # JD
}
```

#### List Formatting
```python
raw = {"tags": ["python", "ai", "data"]}

formatted = {
    "tags_comma": ", ".join(raw["tags"]),                 # python, ai, data
    "tags_upper": ", ".join(raw["tags"]).upper(),        # PYTHON, AI, DATA
    "tags_count": len(raw["tags"]),                      # 3
    "tags_bullets": "\\n".join(f"- {t}" for t in raw["tags"])  # Bulleted list
}
```

#### Number Formatting
```python
raw = {"price": 1234.5678, "percentage": 0.156}

formatted = {
    "price": f"${raw['price']:,.2f}",              # $1,234.57
    "price_rounded": f"{raw['price']:.0f}",        # 1235
    "percentage": f"{raw['percentage']:.1%}",      # 15.6%
}
```

#### Date Formatting
```python
from datetime import datetime

raw = {"timestamp": datetime.now()}

formatted = {
    "date": raw["timestamp"].strftime("%Y-%m-%d"),         # 2025-11-26
    "time": raw["timestamp"].strftime("%I:%M %p"),         # 09:30 PM
    "full": raw["timestamp"].strftime("%B %d, %Y"),        # November 26, 2025
}
```

#### Complete Example
```python
from prompt_manager.core.models import Prompt, PromptTemplate, PromptFormat

# Create prompt with simple template
prompt = Prompt(
    id="formatted_report",
    version="1.0.0",
    format=PromptFormat.TEXT,
    template=PromptTemplate(
        content="""
Report: {{title}}
Generated: {{date}}
Status: {{status}}
Tags: {{tags}}
Completion: {{completion}}
        """.strip(),
        variables=["title", "date", "status", "tags", "completion"]
    )
)

# Pre-process all data
raw_data = {
    "title": "quarterly analysis",
    "timestamp": datetime.now(),
    "status_code": "ok",
    "tag_list": ["finance", "q4", "2025"],
    "completion_rate": 0.87
}

formatted_data = {
    "title": raw_data["title"].title(),
    "date": raw_data["timestamp"].strftime("%B %d, %Y"),
    "status": raw_data["status_code"].upper(),
    "tags": ", ".join(raw_data["tag_list"]).upper(),
    "completion": f"{raw_data['completion_rate']:.0%}"
}

# Render
result = prompt.render(formatted_data)
print(result)
```

**Output:**
```
Report: Quarterly Analysis
Generated: November 26, 2025
Status: OK
Tags: FINANCE, Q4, 2025
Completion: 87%
```
```

### Conditional Examples (UPDATE SYNTAX)
**OLD:**
```python
template = """
{% if severity == "high" %}
CRITICAL
{% endif %}
"""
```

**NEW:**
```python
template = """
{{#if is_critical}}
CRITICAL
{{/if}}
"""

# Note: Handlebars doesn't do comparisons in templates
# Pre-process the condition:
data = {
    "is_critical": (severity == "high")  # Evaluate in Python
}
```

### Loop Examples (UPDATE SYNTAX)
**OLD:**
```python
template = """
{% for item in items %}
- {{item}}
{% endfor %}
"""
```

**NEW:**
```python
template = """
{{#each items}}
- {{this}}
{{/each}}
"""

# Or for objects:
template = """
{{#each datasets}}
- {{name}}: {{rows}} rows
{{/each}}
"""
```

## Additional Corrections Needed

### Cell about Template class (DELETE)
The example creating `Template` directly won't work:
```python
from prompt_manager.core.template import Template  # This class doesn't exist for users
```

Replace with Prompt-based example.

### Variable references
Update all examples to use actual YAML structure:
- `prompt.id` (not `prompt.name`)
- `prompt.metadata.description` (not `prompt.description`)
- `prompt.template.content` (not just `prompt.template`)

### Manager initialization
Update ALL examples:
```python
# OLD
pm = PromptManager(prompts_dir="prompts")

# NEW
pm = PromptManager.create(prompt_dir="prompts")
```

### Getting prompts
```python
# OLD
template = pm.get_template("greeting")

# NEW
prompt = pm.get_prompt("greeting")
```

## Summary of Changes

**Replace:**
- Jinja2 → Handlebars (everywhere)
- `name` → `id` (YAML field)
- `description` → `metadata.description`
- `template` → `template.content`
- Filter examples → Python pre-processing examples
- `{% %}` syntax → `{{# }}` syntax
- `get_template()` → `get_prompt()`
- `PromptManager(prompts_dir=...)` → `PromptManager.create(prompt_dir=...)`

**Add:**
- Section on "Why No Filters" (Handlebars design philosophy)
- Comprehensive Python formatting examples (strings, lists, numbers, dates)
- Best practices for data pre-processing
- Handlebars syntax reference table
