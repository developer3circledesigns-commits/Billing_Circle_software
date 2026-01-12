from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    category_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: str = Field("active")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['active', 'inactive']:
            raise ValueError('Status must be either "active" or "inactive"')
        return v

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None

class Category(CategoryBase):
    category_id: str
    account_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

