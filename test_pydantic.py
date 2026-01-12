
from pydantic import BaseModel
from typing import Optional

class CustomerBase(BaseModel):
    customer_type: str = "business" 
    salutation: Optional[str] = None

print("Model defined successfully")
print(CustomerBase(salutation="Mr."))
