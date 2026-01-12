import sys
import os
sys.path.append(os.getcwd())
from app.core.database import db
from app.backend.deps import get_db
from app.backend.routers.invoices import list_invoices
from app.backend.models.user import User
from pydantic import ValidationError
import json

def debug_invoices():
    db.connect()
    database = db.get_db()
    # find admin user
    user_doc = database['users'].find_one({'email': 'admin@billing.com'})
    if not user_doc:
        print("Admin user not found")
        return
    
    user = User(**user_doc)
    
    print(f"Checking invoices for account: {user.account_id}")
    
    try:
        invoices = list_invoices(current_user=user, db=database)
        print(f"Returned {len(invoices)} invoices")
        for inv in invoices:
            print(json.dumps(inv, default=str, indent=2))
    except Exception as e:
        print(f"Error in list_invoices: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_invoices()
