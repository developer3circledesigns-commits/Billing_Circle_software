
import traceback
from pydantic import BaseModel
from typing import Optional

try:
    print("Testing Empty String Default...")
    class ModelStr(BaseModel):
        f: str = ""
    print("ModelStr OK")
    
    print("Testing Float Zero...")
    class ModelFloat(BaseModel):
        f: float = 0.0
    print("ModelFloat OK")
    
    print("Testing Bool False...")
    class ModelBool(BaseModel):
        f: bool = False
    print("ModelBool OK")

except Exception:
    with open('pydantic_error_6.log', 'w') as f:
        traceback.print_exc(file=f)
