from enum import Enum
from pydantic import BaseModel


class ExtractionSource(str, Enum):
    REGEX_WITH_LABEL = "regex_with_label"
    REGEX_WITHOUT_LABEL = "regex_without_label"
    FALLBACK = "fallback"
    NOT_FOUND = "not_found"


class ExtractedField(BaseModel):
    value: str
    confidence: float
    source: ExtractionSource = ExtractionSource.FALLBACK
