from pydantic import BaseModel
from typing import Dict, List
from app.domain.models.extracted_field import ExtractedField
from app.domain.models.line_item import LineItem


class ExtractionResult(BaseModel):
    fields: Dict[str, ExtractedField]
    line_items: List[LineItem]
