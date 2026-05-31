from __future__ import annotations

from airedteam.core.types import Prompt

_GLYPHS = {
    "A": [" A ", "A A", "AAA", "A A", "A A"],
    "B": ["BB ", "B B", "BB ", "B B", "BBB"],
    "C": [" CC", "C  ", "C  ", "C  ", " CC"],
    "D": ["DD ", "D D", "D D", "D D", "DD "],
    "E": ["EEE", "E  ", "EE ", "E  ", "EEE"],
    "F": ["FFF", "F  ", "FF ", "F  ", "F  "],
    "I": ["III", " I ", " I ", " I ", "III"],
    "L": ["L  ", "L  ", "L  ", "L  ", "LLL"],
    "O": [" O ", "O O", "O O", "O O", " O "],
    "S": [" SS", "S  ", " S ", "  S", "SS "],
    "T": ["TTT", " T ", " T ", " T ", " T "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}


class AsciiArtConverter:
    """Render supported characters as simple ASCII-art glyphs."""

    name = "ascii_art"

    async def convert(self, prompt: Prompt) -> Prompt:
        rows = ["", "", "", "", ""]
        for ch in prompt.text.upper():
            glyph = _GLYPHS.get(ch)
            if glyph is None:
                glyph = [ch * 3, ch * 3, ch * 3, ch * 3, ch * 3]
            for i, row in enumerate(glyph):
                rows[i] = f"{rows[i]} {row}" if rows[i] else row
        return Prompt(text="\n".join(rows), metadata=prompt.metadata)
