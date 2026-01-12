from pydantic import BaseModel, ConfigDict, model_validator
from typing import List, Optional
from datetime import datetime

class QuoteItem(BaseModel):
    item_id: str
    item_name: str
    qty: float
    unit: str = "PCS"
    rate: float
    discount_percent: float = 0.0
    tax_percent: float = 18.0
    amount: float # rate * qty
    tax_amount: float
    total: float # amount + tax_amount - discount
    hsn_code: Optional[str] = None
    
    @model_validator(mode='before')
    @classmethod
    def validate_amounts(cls, data: dict) -> dict:
        qty = float(data.get('qty', 0))
        rate = float(data.get('rate', 0))
        tax_percent = float(data.get('tax_percent', 18.0))
        
        if 'amount' not in data or data['amount'] is None:
            data['amount'] = qty * rate
            
        if 'tax_amount' not in data or data['tax_amount'] is None:
            data['tax_amount'] = data['amount'] * (tax_percent / 100)
            
        if 'total' not in data or data['total'] is None:
            data['total'] = data['amount'] + data['tax_amount']
            
        return data

class QuotationBase(BaseModel):
    customer_id: str
    customer_name: str
    quote_date: datetime = datetime.utcnow()
    valid_until: Optional[datetime] = None
    items: List[QuoteItem]
    sub_total: float
    total_tax: float
    total_discount: float = 0.0
    grand_total: float
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    status: str = "draft" # draft, sent, accepted, declined, converted

    @model_validator(mode='before')
    @classmethod
    def validate_dates(cls, data: dict) -> dict:
        for field in ['quote_date', 'valid_until']:
            if field in data and data[field] == "":
                data[field] = None
        return data

class QuotationCreate(QuotationBase):
    pass

class QuotationUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    quote_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    items: Optional[List[QuoteItem]] = None
    sub_total: Optional[float] = None
    total_tax: Optional[float] = None
    total_discount: Optional[float] = None
    grand_total: Optional[float] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    status: Optional[str] = None

class Quotation(QuotationBase):
    quotation_id: str
    account_id: str
    quotation_number: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
