
import traceback
from pydantic import BaseModel
from typing import Optional

try:
    class CustomerBase(BaseModel):
        customer_type: str = "business" 
        salutation: Optional[str] = None
    print("Success")
except Exception:
    with open('pydantic_error.log', 'w') as f:
        traceback.print_exc(file=f)
