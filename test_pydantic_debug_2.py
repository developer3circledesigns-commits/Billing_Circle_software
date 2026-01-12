
import traceback
from pydantic import BaseModel
from typing import Optional, Union

try:
    class CustomerBase(BaseModel):
        customer_type: str = "business" 
        salutation: Union[str, None] = None
    print("Success with Union")
    
    class CustomerBase2(BaseModel):
        salutation: str = None
    print("Success with str = None")

except Exception:
    with open('pydantic_error_2.log', 'w') as f:
        traceback.print_exc(file=f)
