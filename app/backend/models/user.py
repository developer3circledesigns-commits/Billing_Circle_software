from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "owner" # owner, manager

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str
    organization_name: str # Required for signup to create org

# Properties for inviting a user to an existing account
class UserInvite(UserBase):
    password: str

# Properties to return to client
class User(UserBase):
    id: Optional[str] = None
    user_id: Optional[str] = None
    account_id: str
    is_active: bool = True
    subscription: Optional[dict] = None # Injected during retrieval or from account doc

    model_config = ConfigDict(from_attributes=True)

# Properties stored in DB
class UserInDB(User):
    hashed_password: str

# Token Return Schema
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
