from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class WeaverBase(BaseModel):
    weaver_name: str
    display_name: str = ""
    contact_number: str
    email: str = ""
    address: str = ""
    
    # Identity
    gstin: str = ""
    pan_number: str = ""
    website: str = ""
    
    # Vendor Classification
    vendor_type: str = "manufacturer"  # manufacturer, distributor, service_provider, raw_material
    tax_registration_type: str = "registered"  # registered, unregistered, composition
    
    # TDS Settings
    tds_applicable: bool = False
    tds_percentage: float = 0.0
    
    # Banking Details
    bank_name: str = ""
    account_name: str = ""
    account_number: str = ""
    ifsc_code: str = ""
    preferred_payment_mode: str = "bank_transfer"  # cash, bank_transfer, cheque, upi
    
    # Financial Settings
    opening_balance: float = 0.0
    current_balance: float = 0.0
    credit_period_days: int = 0
    payment_terms: str = "net_15" # net_15, net_30, due_on_receipt
    
    cost: float = 0.0
    
    # Performance Tracking
    rating: float = 0.0  # 0-5 stars
    is_verified: bool = False
    last_purchase_date: Optional[datetime] = None
    total_purchases: float = 0.0  # Lifetime purchase value
    outstanding_amount: float = 0.0
    
    status: str = "active" # active, inactive
    notes: str = ""

class WeaverCreate(WeaverBase):
    pass

class WeaverUpdate(BaseModel):
    weaver_name: Optional[str] = None
    display_name: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    pan_number: Optional[str] = None
    vendor_type: Optional[str] = None
    tax_registration_type: Optional[str] = None
    tds_applicable: Optional[bool] = None
    tds_percentage: Optional[float] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    preferred_payment_mode: Optional[str] = None
    opening_balance: Optional[float] = None
    credit_period_days: Optional[int] = None
    payment_terms: Optional[str] = None
    cost: Optional[float] = None
    rating: Optional[float] = None
    is_verified: Optional[bool] = None
    last_purchase_date: Optional[datetime] = None
    total_purchases: Optional[float] = None
    outstanding_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class Weaver(WeaverBase):
    weaver_id: str
    account_id: str
    weaver_code: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
