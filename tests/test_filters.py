"""
Demo showing template features with the current Prompt Manager API.

Note: Prompt Manager uses Handlebars templates, not Jinja2.
Handlebars doesn't have built-in filters like Jinja2.
"""

from prompt_manager.core.models import Prompt, PromptTemplate, PromptFormat, PromptStatus

# Create a prompt programmatically
prompt = Prompt(
    id="filters_demo",
    version="1.0.0",
    format=PromptFormat.TEXT,
    status=PromptStatus.ACTIVE,
    template=PromptTemplate(
        content="""
Name: {{name}}
Tags: {{tags}}
Score: {{score}}
        """.strip(),
        variables=["name", "tags", "score"]
    )
)

# Render the prompt
result = prompt.render({
    "name": "John Doe",
    "tags": "python, ai, data",  # Handlebars doesn't have list join filters
    "score": "3.14"  # Handlebars doesn't have number formatting filters
})

print(result)
print()
print("Note: For advanced formatting (title case, list joins, number rounding),")
print("pre-process your data before passing to render(), or use custom helpers.")
