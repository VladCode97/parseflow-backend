from pydantic import BaseModel


class ExtractedField(BaseModel):
    value: str
    confidence: float
