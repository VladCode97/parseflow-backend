from pydantic import BaseModel


class LineItem(BaseModel):
    sku: str
    description: str
    quantity: float
    tax_rate: float
    unit_price: float
    total: float
    confidence: float
