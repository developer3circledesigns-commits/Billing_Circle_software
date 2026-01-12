from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.backend.models.quotation import Quotation, QuotationCreate, QuotationUpdate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=Quotation)
async def create_quotation(
    quote_in: QuotationCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # 1. Check Plan Limits
    from app.backend.deps import check_plan_limit
    current_count = db["quotations"].count_documents({"account_id": current_user.account_id})
    await check_plan_limit(current_user.account_id, "quotations", current_count)

    # 2. Auto-generate Quote Number (QTN-001)
    count = db["quotations"].count_documents({"account_id": current_user.account_id})
    quote_number = f"QTN-{str(count + 1).zfill(3)}"

    quote_doc = quote_in.dict()
    quote_doc["quotation_id"] = str(uuid.uuid4())
    quote_doc["account_id"] = current_user.account_id
    quote_doc["quotation_number"] = quote_number
    quote_doc["created_at"] = datetime.utcnow()

    db["quotations"].insert_one(quote_doc)
    return db_core.serialize_doc(quote_doc)

@router.get("/", response_model=List[Quotation])
def list_quotations(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"account_id": current_user.account_id}
    if search:
        query["$or"] = [
            {"quotation_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
        ]
    
    quotes = list(db["quotations"].find(query).skip(skip).limit(limit).sort("created_at", pymongo.DESCENDING))
    return db_core.serialize_list(quotes)

@router.get("/{quotation_id}", response_model=Quotation)
def get_quotation(
    quotation_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    quote = db["quotations"].find_one({"quotation_id": quotation_id, "account_id": current_user.account_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return db_core.serialize_doc(quote)

@router.put("/{quotation_id}", response_model=Quotation)
async def update_quotation(
    quotation_id: str,
    quote_in: QuotationUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"quotation_id": quotation_id, "account_id": current_user.account_id}
    old_quote = db["quotations"].find_one(query)
    if not old_quote:
        raise HTTPException(status_code=404, detail="Quotation not found")

    update_data = quote_in.dict(exclude_unset=True)
    
    # Snapshot customer name if changed
    if "customer_id" in update_data and update_data["customer_id"] != old_quote["customer_id"]:
        customer = db["customers"].find_one({
            "customer_id": update_data["customer_id"], 
            "account_id": current_user.account_id
        })
        if customer:
            update_data["customer_name"] = customer.get("customer_name", "")

    if update_data:
        db["quotations"].update_one(query, {"$set": update_data})
    
    return db_core.serialize_doc(db["quotations"].find_one(query))

@router.delete("/{quotation_id}")
def delete_quotation(
    quotation_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    db["quotations"].delete_one({"quotation_id": quotation_id, "account_id": current_user.account_id})
    return {"message": "Quotation deleted"}

@router.post("/{quotation_id}/email")
async def email_quotation(
    quotation_id: str,
    email_data: dict = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Send quotation via email to customer.
    """
    try:
        quotation = db["quotations"].find_one({
            "quotation_id": quotation_id,
            "account_id": current_user.account_id
        })
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        # Get organization details
        org = db["organizations"].find_one({"account_id": current_user.account_id})
        
        # Get customer details if available
        customer_email = ""
        if quotation.get("customer_id"):
            customer = db["customers"].find_one({
                "customer_id": quotation["customer_id"],
                "account_id": current_user.account_id
            })
            if customer:
                customer_email = customer.get("email", "")
        
        if email_data and email_data.get("email"):
            customer_email = email_data["email"]
        
        if not customer_email:
            raise HTTPException(
                status_code=400,
                detail="Customer email not found. Please add customer email address."
            )
        
        # Prepare email content
        subject = f"Quotation {quotation.get('quotation_number')} from {org.get('company_name', 'Our Company') if org else 'Our Company'}"
        
        body = f"""
Dear {quotation.get('customer_name', 'Customer')},

Please find your quotation details below:

Quotation Number: {quotation.get('quotation_number')}
Quotation Date: {quotation.get('quote_date')}
Valid Until: {quotation.get('valid_until')}

Total Amount: ₹{quotation.get('grand_total', 0):,.2f}

You can view and download your quotation here:
{email_data.get('quotation_url', 'View in your account') if email_data else 'View in your account'}

Thank you for your interest!

Best regards,
{org.get('company_name', 'Our Company') if org else 'Our Company'}
{org.get('email', '') if org else ''}
{org.get('phone', '') if org else ''}
"""
        
        # TODO: Implement actual email sending
        return {
            "status": "success",
            "message": f"Quotation {quotation.get('quotation_number')} email prepared for {customer_email}",
            "recipient": customer_email,
            "subject": subject,
            "note": "Email functionality requires SMTP configuration. Email details prepared successfully."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending quotation email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send quotation email: {str(e)}"
        )

@router.post("/{quotation_id}/duplicate")
async def duplicate_quotation(
    quotation_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Duplicate an existing quotation.
    """
    try:
        # Fetch source quotation
        source_quotation = db["quotations"].find_one({
            "quotation_id": quotation_id,
            "account_id": current_user.account_id
        })
        if not source_quotation:
            raise HTTPException(status_code=404, detail="Source quotation not found")
        
        # Get next quotation number
        count = db["quotations"].count_documents({"account_id": current_user.account_id})
        quote_number = f"QTN-{str(count + 1).zfill(3)}"
        
        # Create new quotation based on source
        new_quotation = source_quotation.copy()
        new_quotation.update({
            "quotation_id": str(uuid.uuid4()),
            "quotation_number": quote_number,
            "quote_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        })
        
        # Remove MongoDB internal ID and invoice reference
        if "_id" in new_quotation:
            del new_quotation["_id"]
        if "invoice_id" in new_quotation:
            del new_quotation["invoice_id"]
        
        db["quotations"].insert_one(new_quotation)
        
        return {
            "status": "success",
            "message": "Quotation duplicated successfully",
            "new_quotation_id": new_quotation["quotation_id"],
            "quotation_number": quote_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error duplicating quotation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to duplicate quotation: {str(e)}"
        )

