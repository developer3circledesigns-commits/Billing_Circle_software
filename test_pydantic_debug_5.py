
import traceback
from pydantic import BaseModel
from typing import Any

try:
    print("Testing Any...")
    class ModelAny(BaseModel):
        f: Any = None
    print("ModelAny OK")

    print("Testing Union Syntax...")
    class ModelUnion(BaseModel):
        f: str | None = None
    print("ModelUnion OK")
    
    # Testing direct import Optional again just in case
    from typing import Optional
    print("Testing Optional with alias...")
    class ModelOpt(BaseModel):
        f: Optional[str]
    print("ModelOpt OK (No default)")

except Exception:
    with open('pydantic_error_5.log', 'w') as f:
        traceback.print_exc(file=f)
