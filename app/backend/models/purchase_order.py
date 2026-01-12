from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class POLineItem(BaseModel):
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

class PurchaseOrderBase(BaseModel):
    weaver_id: str
    weaver_name: str
    weaver_code: str
    po_date: datetime
    expected_delivery_date: Optional[datetime] = None
    
    items: List[POLineItem]
    
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    
    status: str = "draft"  # draft, sent, confirmed, partially_received, received, cancelled
    
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    
    # Receiving tracking
    received_qty: Optional[float] = 0.0
    pending_qty: Optional[float] = 0.0

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderUpdate(BaseModel):
    weaver_id: Optional[str] = None
    weaver_name: Optional[str] = None
    po_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    items: Optional[List[POLineItem]] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    received_qty: Optional[float] = None
    pending_qty: Optional[float] = None

class PurchaseOrder(PurchaseOrderBase):
    po_id: str
    account_id: str
    po_number: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
