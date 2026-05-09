import re


class NormalizationService:

    def normalize(self, text: str) -> str:
        normalized_text = text
        normalized_text = self._remove_extra_spaces(normalized_text)
        normalized_text = self._normalize_line_breaks(normalized_text)
        normalized_text = self._remove_special_characters(normalized_text)
        return normalized_text

    def _remove_extra_spaces(self, text: str) -> str:
        lines = text.split("\n")
        normalized_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
        return "\n".join(line for line in normalized_lines if line)

    def _normalize_line_breaks(self, text: str) -> str:
        return re.sub(r"\n+", "\n", text)

    def _remove_special_characters(self, text: str) -> str:
        return re.sub(r"[^\w\s\n\-\.\:/#]", "", text)
