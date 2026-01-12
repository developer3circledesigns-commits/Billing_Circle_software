from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PaymentBase(BaseModel):
    account_id: str
    party_id: str # Customer ID or Weaver ID
    party_name: str
    amount: float
    payment_date: datetime = datetime.utcnow()
    payment_mode: str = "cash" # cash, bank, upi, cheque
    reference_number: Optional[str] = None
    invoice_id: Optional[str] = None # Link to invoice if customer payment
    payment_type: str = "receive" # receive (from customer) or pay (to weaver)
    notes: Optional[str] = None

class PaymentCreate(BaseModel):
    party_id: str
    party_name: str
    amount: float
    payment_date: Optional[datetime] = None
    payment_mode: str
    reference_number: Optional[str] = None
    invoice_id: Optional[str] = None
    payment_type: str
    notes: Optional[str] = None

class Payment(PaymentBase):
    payment_id: str
    payment_number: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
