from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    item_name: str
    item_type: str = "goods" # goods, service
    sku: str = ""
    brand: str = ""
    category_id: Optional[str] = None
    hsn_code: str = ""
    unit: str = "PCS" # PCS, BOX, KGS, etc.
    
    # Financial Settings
    tax_preference: str = "taxable" # taxable, exempt
    tax_rate: float = 18.0
    purchase_price: float = 0.0
    selling_price: float = 0.0
    
    # Inventory Settings
    reorder_level: int = 10 # reorder_point
    opening_stock: float = 0.0
    opening_stock_rate: float = 0.0
    preferred_supplier_id: str = ""
    
    status: str = "active" # active, inactive
    description: str = ""
    notes: str = ""

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    sku: Optional[str] = None
    brand: Optional[str] = None
    category_id: Optional[str] = None
    hsn_code: Optional[str] = None
    unit: Optional[str] = None
    tax_preference: Optional[str] = None
    tax_rate: Optional[float] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    reorder_level: Optional[int] = None
    opening_stock: Optional[float] = None
    opening_stock_rate: Optional[float] = None
    preferred_supplier_id: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class Item(ItemBase):
    item_id: str
    account_id: str
    created_at: datetime
    current_stock: float = 0.0

    model_config = ConfigDict(from_attributes=True)
