from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class BillLineItem(BaseModel):
    item_id: str
    item_name: str
    item_code: Optional[str] = None
    description: Optional[str] = None
    qty: float
    unit: str = "PCS"
    rate: float
    tax_rate: float = 18.0
    tax_amount: float = 0.0
    amount: float = 0.0

class PurchaseBillBase(BaseModel):
    weaver_id: str
    weaver_name: str
    weaver_code: str
    
    po_id: Optional[str] = None  # Link to purchase order if created from PO
    po_number: Optional[str] = None
    
    bill_date: datetime
    due_date: datetime
    
    vendor_bill_number: Optional[str] = None  # Vendor's own bill number
    
    items: List[BillLineItem]
    
    subtotal: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    paid_amount: float = 0.0
    balance_amount: float = 0.0
    
    payment_status: str = "unpaid"  # unpaid, partial, paid, overdue
    status: str = "draft"  # draft, submitted, approved, paid
    
    notes: Optional[str] = None
    attachments: Optional[List[str]] = []

class PurchaseBillCreate(PurchaseBillBase):
    pass

class PurchaseBillUpdate(BaseModel):
    weaver_id: Optional[str] = None
    weaver_name: Optional[str] = None
    po_id: Optional[str] = None
    bill_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    vendor_bill_number: Optional[str] = None
    items: Optional[List[BillLineItem]] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    total_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    balance_amount: Optional[float] = None
    payment_status: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[List[str]] = None

class PurchaseBill(PurchaseBillBase):
    bill_id: str
    account_id: str
    bill_number: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
