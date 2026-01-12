from pydantic import BaseModel, ConfigDict, model_validator
from typing import List, Optional
from datetime import datetime

class InvoiceItem(BaseModel):
    item_id: str
    item_name: str
    qty: float
    unit: str = "PCS"
    rate: float
    tax_percent: float = 18.0
    tax_amount: float
    total: Optional[float] = None
    hsn_code: Optional[str] = None
    # Removed amount_received from here as it belongs to the Invoice level
    
    @model_validator(mode='before')
    @classmethod
    def validate_amounts(cls, data: dict) -> dict:
        if 'amount' in data and ('total' not in data or data['total'] is None):
            data['total'] = data['amount']
        
        # Ensure qty and rate are present for tax calculation
        qty = data.get('qty')
        rate = data.get('rate')
        tax_percent = data.get('tax_percent', 18.0)
        
        if qty is not None and rate is not None:
            if 'tax_amount' not in data or data['tax_amount'] is None:
                data['tax_amount'] = float(qty) * float(rate) * (float(tax_percent) / 100)
            if 'total' not in data or data['total'] is None:
                data['total'] = (float(qty) * float(rate)) + data['tax_amount']
        
        return data

class InvoiceBase(BaseModel):
    customer_id: str
    customer_name: str
    # Snapshot fields for persistence
    customer_address: Optional[str] = None
    customer_city: Optional[str] = None
    customer_state: Optional[str] = None
    customer_state_code: Optional[str] = None
    customer_pincode: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_gstin: Optional[str] = None
    
    invoice_date: datetime = datetime.utcnow()
    due_date: Optional[datetime] = None
    items: List[InvoiceItem]
    sub_total: float
    total_tax: float
    grand_total: float
    payment_status: str = "unpaid" # unpaid, partial, paid
    amount_received: float = 0.0
    balance_amount: float
    status: str = "active" # active, cancelled
    quotation_id: Optional[str] = None
    quotation_number: Optional[str] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    discount_amount: Optional[float] = 0.0
    shipping_charges: Optional[float] = 0.0


class InvoiceCreate(InvoiceBase):
    @model_validator(mode='before')
    @classmethod
    def validate_create_data(cls, data: dict) -> dict:
        if 'due_date' in data and data['due_date'] == "":
            data['due_date'] = None
        if 'invoice_date' in data and data['invoice_date'] == "":
            data['invoice_date'] = datetime.utcnow()
        
        # Calculate balance_amount if missing
        if 'balance_amount' not in data or data['balance_amount'] is None:
            grand_total = float(data.get('grand_total', 0))
            amount_received = float(data.get('amount_received', 0))
            data['balance_amount'] = grand_total - amount_received
            
        return data

class InvoiceUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_city: Optional[str] = None
    customer_state: Optional[str] = None
    customer_state_code: Optional[str] = None
    customer_pincode: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_gstin: Optional[str] = None
    
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    items: Optional[List[InvoiceItem]] = None
    sub_total: Optional[float] = None
    total_tax: Optional[float] = None
    grand_total: Optional[float] = None
    payment_status: Optional[str] = None
    amount_received: Optional[float] = None
    balance_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    discount_amount: Optional[float] = None
    shipping_charges: Optional[float] = None
    payment_terms: Optional[str] = None

class Invoice(InvoiceBase):
    invoice_id: str
    account_id: str
    invoice_number: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
