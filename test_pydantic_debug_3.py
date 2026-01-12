
import traceback
from pydantic import BaseModel, Field
from typing import Optional

try:
    class CustomerBase(BaseModel):
        customer_type: str = "business" 
        salutation: Optional[str] = Field(default=None)
    
    print("Success with Field")

except Exception:
    with open('pydantic_error_3.log', 'w') as f:
        traceback.print_exc(file=f)
