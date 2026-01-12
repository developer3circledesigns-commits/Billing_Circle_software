
import traceback
from pydantic import BaseModel
from typing import Optional

try:
    print("Testing Required str...")
    class Model1(BaseModel):
        f: str
    print("Model1 OK")

    print("Testing Default str...")
    class Model2(BaseModel):
        f: str = "default"
    print("Model2 OK")

    print("Testing String Forward Ref...")
    class Model3(BaseModel):
        f: "Optional[str]" = None
    print("Model3 OK")
    
    print("Testing New Union...")
    class Model4(BaseModel):
        f: str | None = None
    print("Model4 OK")

except Exception:
    with open('pydantic_error_4.log', 'w') as f:
        traceback.print_exc(file=f)
