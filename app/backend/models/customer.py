from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    customer_type: str = "business" # business, individual
    salutation: str = ""
    first_name: str = ""
    last_name: str = ""
    customer_name: str # Still primary display name
    company_name: str = ""
    display_name: str = ""
    
    contact_number: Optional[str] = "" # Work Phone
    mobile_number: str = ""
    email: str = ""
    website: str = ""
    language: str = "English"
    
    # Identity
    gstin: str = ""
    pan_number: str = ""
    
    # Financial Settings
    currency: str = "INR"
    opening_balance: float = 0.0
    current_balance: float = 0.0
    payment_terms: str = "due_on_receipt"
    enable_portal: bool = False
    
    # Addresses
    billing_address_attention: str = ""
    billing_address: str = "" # Street
    billing_city: str = ""
    billing_state: str = ""
    billing_zip: str = ""
    billing_country: str = ""
    billing_phone: str = ""
    
    shipping_address_attention: str = ""
    shipping_address: str = "" # Street
    shipping_city: str = ""
    shipping_state: str = ""
    shipping_zip: str = ""
    shipping_country: str = ""
    shipping_phone: str = ""
    
    status: str = "active"
    notes: str = ""

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    customer_type: str = ""
    salutation: str = ""
    first_name: str = ""
    last_name: str = ""
    customer_name: str = ""
    company_name: str = ""
    display_name: str = ""
    contact_number: str = ""
    mobile_number: str = ""
    email: str = ""
    website: str = ""
    language: str = ""
    
    gstin: str = ""
    pan_number: str = ""
    
    currency: str = ""
    opening_balance: float = 0.0
    payment_terms: str = ""
    enable_portal: bool = False
    
    billing_address_attention: str = ""
    billing_address: str = ""
    billing_city: str = ""
    billing_state: str = ""
    billing_zip: str = ""
    billing_country: str = ""
    billing_phone: str = ""
    
    shipping_address_attention: str = ""
    shipping_address: str = ""
    shipping_city: str = ""
    shipping_state: str = ""
    shipping_zip: str = ""
    shipping_country: str = ""
    shipping_phone: str = ""
    
    status: str = ""
    notes: str = ""

class Customer(CustomerBase):
    customer_id: str
    account_id: str
    customer_code: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
