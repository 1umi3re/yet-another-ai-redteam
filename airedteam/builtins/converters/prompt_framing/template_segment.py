from __future__ import annotations

from airedteam.core.types import Prompt


class TemplateSegmentConverter:
    """Insert prompt text into a template with explicit segment separators."""

    name = "template_segment"

    def __init__(self, *, template: str = "{prompt}", segment_separator: str = "|||") -> None:
        if "{prompt}" not in template:
            raise ValueError("template_segment template must contain '{prompt}'")
        self.template = template
        self.segment_separator = segment_separator

    async def convert(self, prompt: Prompt) -> Prompt:
        segmented = f"{self.segment_separator}{prompt.text}{self.segment_separator}"
        return Prompt(text=self.template.format(prompt=segmented), metadata=prompt.metadata)
