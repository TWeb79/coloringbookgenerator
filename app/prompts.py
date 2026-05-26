"""Prompt templates for KidsColorAI story generation"""

CHILDREN_SYSTEM_PROMPT = (
    "You are a children's storybook writer. Write a very short, simple story "
    "paragraph for each page. Keep sentences short. Use exciting language for kids. "
    "Do not use complex words. Always keep content safe for children (5-12 years). "
    "No violence, no profanity."
)

CHARACTER_SYSTEM_PROMPT = (
    "You are a children's storybook character designer. Create a main character "
    "for a coloring book story. The character should be simple, memorable, and "
    "consistent across all pages. Include clear visual details for illustration."
)

CHARACTER_PROMPT_TEMPLATE = """Theme: {theme}

Create a main character for this coloring book story. Respond in JSON format with these fields:
- name: The character's name (simple, kid-friendly)
- description: A brief description of the character (1-2 sentences)
- appearance: Visual details for illustration (simple, clear lines, specific colors if applicable)
- personality: How the character behaves (adjective + brief description)
- key_features: A list of 3-5 distinctive visual features that make this character recognizable
- color_palette: Main colors used for the character (e.g., "green body, blue eyes, yellow spots")"""

STORY_PLAN_PROMPT_TEMPLATE = """Theme: {theme}
Total Pages: {page_count}
Main Character: {char_name} - {char_appearance}
Key Features: {key_features}
Color Palette: {color_palette}

Create a story broken down into pages. For each page, provide:
- page_number: (1 to {page_count})
- story_text: A short, simple paragraph for the page
- image_prompt: A detailed prompt for a coloring book illustration featuring {char_name}.
  The character appears as: {char_appearance}.
  Key features to include: {key_features}.
  Colors: {color_palette}.
  Include clear visual elements suitable for children's coloring book.
  Always include the same character appearance in each prompt.

Respond as a JSON array of objects."""

IMAGE_PROMPT_SUFFIX = ", coloring book style, thick black outlines, white background, high contrast line art, simple shapes for children"