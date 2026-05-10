from pydantic import BaseModel
from typing import List
from app.domain.models.extracted_field import ExtractionSource


class FieldResultSchema(BaseModel):
    value: str
    confidence: float
    source: ExtractionSource


class LineItemSchema(BaseModel):
    sku: str
    description: str
    quantity: float
    tax_rate: float
    unit_price: float
    total: float
    confidence: float


class ProcessingResponseSchema(BaseModel):
    fields: dict[str, FieldResultSchema]
    line_items: List[LineItemSchema]
