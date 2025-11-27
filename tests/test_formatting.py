"""
Best practice: Pre-process data for formatting before rendering.

Since Handlebars doesn't have Jinja2-style filters, format your data
in Python before passing it to the template.
"""

from prompt_manager.core.models import Prompt, PromptTemplate, PromptFormat

# Create a prompt
prompt = Prompt(
    id="formatted_demo",
    version="1.0.0",
    format=PromptFormat.TEXT,
    template=PromptTemplate(
        content="""
Name: {{name}}
Tags: {{tags}}
Score: {{score}}
        """.strip(),
        variables=["name", "tags", "score"]
    )
)

# Pre-process data with Python's built-in formatting
raw_data = {
    "name": "john doe",
    "tags": ["python", "ai", "data"],
    "score": 3.14159
}

# Format the data before rendering
formatted_data = {
    "name": raw_data["name"].title(),  # Title case
    "tags": ", ".join(raw_data["tags"]).upper(),  # Join and uppercase
    "score": f"{raw_data['score']:.2f}"  # Round to 2 decimals
}

# Render with formatted data
result = prompt.render(formatted_data)

print(result)
print()
print("✓ Data formatted using Python before rendering")
