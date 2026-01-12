from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class VendorPaymentBase(BaseModel):
    weaver_id: str
    weaver_name: str
    
    bill_id: Optional[str] = None  # Link to specific bill if applicable
    bill_number: Optional[str] = None
    
    payment_date: datetime
    amount: float
    
    payment_mode: str = "bank_transfer"  # cash, bank_transfer, cheque, upi, card
    reference_number: Optional[str] = None
    
    notes: Optional[str] = None

class VendorPaymentCreate(VendorPaymentBase):
    pass

class VendorPaymentUpdate(BaseModel):
    payment_date: Optional[datetime] = None
    amount: Optional[float] = None
    payment_mode: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class VendorPayment(VendorPaymentBase):
    payment_id: str
    account_id: str
    payment_number: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
