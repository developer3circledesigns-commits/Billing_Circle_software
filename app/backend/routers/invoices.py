from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.backend.models.invoice import Invoice, InvoiceCreate, InvoiceUpdate, InvoiceItem
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db, check_plan_limit
from app.core.database import db as db_core
import uuid
from datetime import datetime, date
import pymongo
from decimal import Decimal
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=Invoice)
async def create_invoice(
    invoice_in: InvoiceCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Create a new invoice with stock validation and automatic invoice number generation.
    Resilient numbering logic avoids crashes on non-standard formats.
    """
    try:
        # 1. Check Plan Limits
        current_count = db["invoices"].count_documents({
            "account_id": current_user.account_id, 
            "status": {"$ne": "cancelled"}
        })
        await check_plan_limit(current_user.account_id, "invoices", current_count + 1)

        # 2. Validate customer exists and snapshot data
        customer = db["customers"].find_one({
            "customer_id": invoice_in.customer_id, 
            "account_id": current_user.account_id
        })
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found with ID: {invoice_in.customer_id}"
            )

        # 3. Robust Invoice Numbering
        # Find the latest invoice to determine the next number
        last_invoice = db["invoices"].find_one(
            {"account_id": current_user.account_id},
            sort=[("created_at", pymongo.DESCENDING)]
        )
        
        new_num = 1
        if last_invoice and "invoice_number" in last_invoice:
            try:
                # Attempt to extract numeric part from "INV-XXXX"
                parts = last_invoice["invoice_number"].split('-')
                if len(parts) > 1:
                    new_num = int(parts[1]) + 1
                else:
                    new_num = current_count + 1
            except (ValueError, IndexError):
                new_num = current_count + 1
        
        invoice_number = f"INV-{str(new_num).zfill(4)}"

        # 4. Stock Validation
        for item in invoice_in.items:
            item_doc = db["items"].find_one({
                "item_id": item.item_id, 
                "account_id": current_user.account_id
            })
            if not item_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item {item.item_name} not found"
                )
            
            current_stock = item_doc.get("current_stock", 0)
            if current_stock < item.qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {item.item_name}. Available: {current_stock}, Requested: {item.qty}"
                )

        # 5. Prepare Document
        invoice_doc = invoice_in.dict()
        invoice_doc.update({
            "invoice_id": str(uuid.uuid4()),
            "account_id": current_user.account_id,
            "user_id": current_user.user_id,
            "invoice_number": invoice_number,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "customer_name": customer.get("customer_name", ""),
            "customer_code": customer.get("customer_code", ""),
            "customer_address": customer.get("billing_address", ""),
            "customer_city": customer.get("billing_city", ""),
            "customer_state": customer.get("billing_state", ""),
            "customer_state_code": customer.get("state_code", ""), # assuming this exists or is empty
            "customer_pincode": customer.get("billing_zip", ""),
            "customer_phone": customer.get("mobile_number", customer.get("billing_phone", "")),
            "customer_email": customer.get("email", ""),
            "customer_gstin": customer.get("gstin", "")
        })

        # Recalculate totals to ensure precision
        sub_total = sum(item.qty * item.rate for item in invoice_in.items)
        total_tax = sum(item.qty * item.rate * (item.tax_percent / 100) for item in invoice_in.items)
        
        # Apply discount and shipping
        discount = invoice_in.discount_amount or 0
        shipping = invoice_in.shipping_charges or 0
        grand_total = sub_total + total_tax - discount + shipping
        
        invoice_doc["sub_total"] = float(round(sub_total, 2))
        invoice_doc["total_tax"] = float(round(total_tax, 2))
        invoice_doc["grand_total"] = float(round(grand_total, 2))
        invoice_doc["discount_amount"] = float(round(discount, 2))
        invoice_doc["shipping_charges"] = float(round(shipping, 2))
        
        # Payment Logic
        if invoice_doc["payment_status"] == "paid":
            invoice_doc["balance_amount"] = 0
            invoice_doc["amount_received"] = invoice_doc["grand_total"]
        elif invoice_doc["payment_status"] == "partial":
            # amount_received should be provided by frontend
            invoice_doc["balance_amount"] = max(0, invoice_doc["grand_total"] - invoice_doc.get("amount_received", 0))
        else:
            invoice_doc["payment_status"] = "unpaid"
            invoice_doc["balance_amount"] = invoice_doc["grand_total"]
            invoice_doc["amount_received"] = 0

        # 6. Handle Quotation Conversion
        if invoice_in.quotation_id:
            quotation = db["quotations"].find_one({
                "quotation_id": invoice_in.quotation_id, 
                "account_id": current_user.account_id
            })
            if quotation:
                if quotation.get("status") == "converted":
                    # We allow it, but log it; or could raise error. 
                    # Let's just update it to be safe.
                    pass
                db["quotations"].update_one(
                    {"quotation_id": invoice_in.quotation_id, "account_id": current_user.account_id},
                    {"$set": {"status": "converted", "updated_at": datetime.utcnow()}}
                )
                invoice_doc["quotation_number"] = quotation.get("quotation_number")

        # 7. Finalize Creation and Stock Updates
        db["invoices"].insert_one(invoice_doc)
        
        for item in invoice_in.items:
            db["items"].update_one(
                {"item_id": item.item_id, "account_id": current_user.account_id},
                {
                    "$inc": {"current_stock": -item.qty},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Stock Transaction Log
            stock_transaction = {
                "transaction_id": str(uuid.uuid4()),
                "item_id": item.item_id,
                "item_name": item.item_name,
                "invoice_id": invoice_doc["invoice_id"],
                "invoice_number": invoice_number,
                "account_id": current_user.account_id,
                "transaction_type": "out",
                "quantity": item.qty,
                "transaction_date": datetime.utcnow(),
                "notes": f"Sold via invoice {invoice_number}"
            }
            db["stock_transactions"].insert_one(stock_transaction)

        # 8. Create Payment Record (if any amount received)
        if invoice_doc.get("amount_received", 0) > 0:
            payment_doc = {
                "payment_id": str(uuid.uuid4()),
                "invoice_id": invoice_doc["invoice_id"],
                "invoice_number": invoice_number,
                "account_id": current_user.account_id,
                "customer_id": invoice_in.customer_id,
                "customer_name": invoice_doc["customer_name"],
                "amount": invoice_doc["amount_received"],
                "payment_date": datetime.utcnow(),
                "payment_method": "cash", 
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            db["payments"].insert_one(payment_doc)

        return db_core.serialize_doc(invoice_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backend processing failure: {str(e)}"
        )

@router.get("/", response_model=List[Invoice])
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    customer_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[str] = None,
    payment_status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    List invoices with filtering and pagination
    """
    try:
        query = {"account_id": current_user.account_id}
        
        # Search filter
        if search:
            query["$or"] = [
                {"invoice_number": {"$regex": search, "$options": "i"}},
                {"customer_name": {"$regex": search, "$options": "i"}},
                {"customer_code": {"$regex": search, "$options": "i"}},
            ]
        
        # Customer filter
        if customer_id:
            query["customer_id"] = customer_id
        
        # Date range filter
        if start_date or end_date:
            query["invoice_date"] = {}
            if start_date:
                query["invoice_date"]["$gte"] = start_date.isoformat()
            if end_date:
                query["invoice_date"]["$lte"] = end_date.isoformat()
        
        # Status filter
        if status_filter:
            query["status"] = status_filter
        else:
            query["status"] = {"$ne": "cancelled"}
        
        # Payment status filter
        if payment_status:
            query["payment_status"] = payment_status
        
        # Execute query with pagination
        invoices = list(db["invoices"].find(query)
                       .skip(skip)
                       .limit(limit)
                       .sort("created_at", pymongo.DESCENDING))
        
        # Calculate total count for pagination info
        total_count = db["invoices"].count_documents(query)
        
        # Add pagination metadata to response
        response = db_core.serialize_list(invoices)
        for inv in response:
            inv["_total_count"] = total_count
        
        return response
        
    except Exception as e:
        print(f"Error listing invoices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving invoices"
        )

@router.get("/{invoice_id}", response_model=Invoice)
def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Get a specific invoice by ID
    """
    try:
        invoice = db["invoices"].find_one({
            "invoice_id": invoice_id, 
            "account_id": current_user.account_id
        })
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # Get payment history for this invoice
        payments = list(db["payments"].find({
            "invoice_id": invoice_id,
            "account_id": current_user.account_id
        }).sort("payment_date", pymongo.DESCENDING))
        
        result = db_core.serialize_doc(invoice)
        result["payments"] = db_core.serialize_list(payments)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving invoice"
        )

@router.get("/number/{invoice_number}", response_model=Invoice)
def get_invoice_by_number(
    invoice_number: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Get invoice by invoice number
    """
    try:
        invoice = db["invoices"].find_one({
            "invoice_number": invoice_number, 
            "account_id": current_user.account_id
        })
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice not found with number: {invoice_number}"
            )
        
        return db_core.serialize_doc(invoice)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting invoice by number: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving invoice"
        )

@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice(
    invoice_id: str,
    invoice_in: InvoiceUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Update invoice details, including items and stock adjustments.
    """
    try:
        query = {"invoice_id": invoice_id, "account_id": current_user.account_id}
        old_invoice = db["invoices"].find_one(query)
        
        if not old_invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        if old_invoice.get("status") == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a cancelled invoice"
            )
        
        update_data = invoice_in.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        # Handle Item and Stock Updates
        if "items" in update_data:
            # 1. Revert stock for all OLD items
            for old_item in old_invoice.get("items", []):
                db["items"].update_one(
                    {"item_id": old_item["item_id"], "account_id": current_user.account_id},
                    {"$inc": {"current_stock": old_item["qty"]}}
                )
                # Log Reversal
                db["stock_transactions"].insert_one({
                    "transaction_id": str(uuid.uuid4()),
                    "item_id": old_item["item_id"],
                    "item_name": old_item["item_name"],
                    "invoice_id": invoice_id,
                    "account_id": current_user.account_id,
                    "transaction_type": "in",
                    "quantity": old_item["qty"],
                    "transaction_date": datetime.utcnow(),
                    "notes": f"Stock reverted for invoice update: {old_invoice.get('invoice_number')}"
                })

            # 2. Validate and Deduct stock for NEW items
            for new_item in update_data["items"]:
                item_doc = db["items"].find_one({
                    "item_id": new_item["item_id"], 
                    "account_id": current_user.account_id
                })
                if not item_doc:
                    # Rolling back might be complex here, but since we are in a try/except, 
                    # we should ideally do this in a transaction. 
                    # For now, we raise error and user has to fix.
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Item {new_item['item_name']} not found"
                    )
                
                if item_doc.get("current_stock", 0) < new_item["qty"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for {new_item['item_name']}. Available: {item_doc.get('current_stock', 0)}, Requested: {new_item['qty']}"
                    )
                
                db["items"].update_one(
                    {"item_id": new_item["item_id"], "account_id": current_user.account_id},
                    {"$inc": {"current_stock": -new_item["qty"]}}
                )
                
                # Log New Deduction
                db["stock_transactions"].insert_one({
                    "transaction_id": str(uuid.uuid4()),
                    "item_id": new_item["item_id"],
                    "item_name": new_item["item_name"],
                    "invoice_id": invoice_id,
                    "account_id": current_user.account_id,
                    "transaction_type": "out",
                    "quantity": new_item["qty"],
                    "transaction_date": datetime.utcnow(),
                    "notes": f"Stock deducted for invoice update: {old_invoice.get('invoice_number')}"
                })

        # Handle customer name snapshot if customer_id changed
        if "customer_id" in update_data and update_data["customer_id"] != old_invoice["customer_id"]:
            customer = db["customers"].find_one({
                "customer_id": update_data["customer_id"], 
                "account_id": current_user.account_id
            })
            if customer:
                update_data["customer_name"] = customer.get("customer_name", "")
                update_data["customer_address"] = customer.get("billing_address", "")
                update_data["customer_gstin"] = customer.get("gstin", "")
        
        # Handle payment status/balance updates logic (similar to create)
        if "grand_total" in update_data or "amount_received" in update_data:
            g_total = update_data.get("grand_total", old_invoice.get("grand_total", 0))
            a_received = update_data.get("amount_received", old_invoice.get("amount_received", 0))
            
            update_data["balance_amount"] = max(0, g_total - a_received)
            if update_data["balance_amount"] == 0:
                update_data["payment_status"] = "paid"
            elif a_received > 0:
                update_data["payment_status"] = "partial"
            else:
                update_data["payment_status"] = "unpaid"
        
        if update_data:
            db["invoices"].update_one(query, {"$set": update_data})
            
        # Fetch and return the updated invoice
        updated_invoice = db["invoices"].find_one(query)
        if not updated_invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found after update"
            )
        
        return db_core.serialize_doc(updated_invoice)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating invoice: {str(e)}"
        )

@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Soft delete - mark as cancelled and revert stock
    """
    try:
        query = {"invoice_id": invoice_id, "account_id": current_user.account_id}
        invoice = db["invoices"].find_one(query)
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        if invoice.get("status") == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice is already cancelled"
            )

        # 1. Revert stock
        for item in invoice.get("items", []):
            db["items"].update_one(
                {
                    "item_id": item["item_id"], 
                    "account_id": current_user.account_id
                },
                {
                    "$inc": {"current_stock": item["qty"]},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Create stock transaction record for reversal
            stock_transaction = {
                "transaction_id": str(uuid.uuid4()),
                "item_id": item["item_id"],
                "item_name": item["item_name"],
                "invoice_id": invoice_id,
                "invoice_number": invoice.get("invoice_number"),
                "account_id": current_user.account_id,
                "transaction_type": "in",
                "quantity": item["qty"],
                "previous_stock": db["items"].find_one({
                    "item_id": item["item_id"], 
                    "account_id": current_user.account_id
                }).get("current_stock", 0) - item["qty"],  # Subtract to get previous
                "new_stock": db["items"].find_one({
                    "item_id": item["item_id"], 
                    "account_id": current_user.account_id
                }).get("current_stock", 0),
                "transaction_date": datetime.utcnow(),
                "notes": f"Stock reverted due to invoice cancellation: {invoice.get('invoice_number')}"
            }
            db["stock_transactions"].insert_one(stock_transaction)

        # 2. Revert quotation status if applicable
        if invoice.get("quotation_id"):
            db["quotations"].update_one(
                {
                    "quotation_id": invoice["quotation_id"], 
                    "account_id": current_user.account_id
                },
                {
                    "$set": {
                        "status": "active", 
                        "updated_at": datetime.utcnow()
                    }
                }
            )

        # 3. Mark invoice as cancelled
        db["invoices"].update_one(
            query, 
            {
                "$set": {
                    "status": "cancelled", 
                    "balance_amount": 0,
                    "updated_at": datetime.utcnow(),
                    "cancelled_at": datetime.utcnow()
                }
            }
        )

        # 4. Mark related payments as cancelled
        db["payments"].update_many(
            {
                "invoice_id": invoice_id,
                "account_id": current_user.account_id
            },
            {
                "$set": {
                    "status": "cancelled",
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return {
            "message": "Invoice cancelled successfully",
            "invoice_id": invoice_id,
            "invoice_number": invoice.get("invoice_number")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error cancelling invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cancelling invoice"
        )

@router.post("/{invoice_id}/add-payment")
def add_payment_to_invoice(
    invoice_id: str,
    payment_data: dict,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Add a payment to an invoice
    """
    try:
        query = {"invoice_id": invoice_id, "account_id": current_user.account_id}
        invoice = db["invoices"].find_one(query)
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        if invoice.get("status") == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add payment to a cancelled invoice"
            )
        
        amount = payment_data.get("amount", 0)
        payment_method = payment_data.get("payment_method", "cash")
        reference_number = payment_data.get("reference_number", "")
        payment_date = payment_data.get("payment_date", datetime.utcnow())
        
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than 0"
            )
        
        # Calculate new balance
        current_balance = invoice.get("balance_amount", invoice.get("grand_total", 0))
        current_received = invoice.get("amount_received", 0)
        
        if amount > current_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount ({amount}) exceeds balance due ({current_balance})"
            )
        
        new_balance = current_balance - amount
        new_received = current_received + amount
        
        # Determine new payment status
        if new_balance <= 0:
            new_payment_status = "paid"
            new_balance = 0
        elif new_received > 0:
            new_payment_status = "partial"
        else:
            new_payment_status = "unpaid"
        
        # Create payment record
        payment = {
            "payment_id": str(uuid.uuid4()),
            "invoice_id": invoice_id,
            "invoice_number": invoice.get("invoice_number"),
            "account_id": current_user.account_id,
            "customer_id": invoice.get("customer_id"),
            "customer_name": invoice.get("customer_name", ""),
            "amount": amount,
            "payment_date": payment_date,
            "payment_method": payment_method,
            "reference_number": reference_number or f"INV-{invoice.get('invoice_number')}-PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "completed",
            "created_at": datetime.utcnow()
        }
        db["payments"].insert_one(payment)
        
        # Update invoice
        update_data = {
            "payment_status": new_payment_status,
            "amount_received": new_received,
            "balance_amount": new_balance,
            "updated_at": datetime.utcnow()
        }
        
        db["invoices"].update_one(query, {"$set": update_data})
        
        return {
            "message": "Payment added successfully",
            "payment_id": payment["payment_id"],
            "new_balance": new_balance,
            "new_payment_status": new_payment_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding payment"
        )

@router.post("/{invoice_id}/email")
async def email_invoice(
    invoice_id: str,
    email_data: dict = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Send invoice via email to customer with invoice details.
    """
    try:
        invoice = db["invoices"].find_one({
            "invoice_id": invoice_id, 
            "account_id": current_user.account_id
        })
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Get organization details for email
        org = db["organizations"].find_one({"account_id": current_user.account_id})
        
        # Determine recipient email
        recipient_email = invoice.get('customer_email', '')
        if email_data and email_data.get('email'):
            recipient_email = email_data['email']
        
        if not recipient_email:
            raise HTTPException(
                status_code=400, 
                detail="Customer email not found. Please add customer email address."
            )
        
        # Prepare email content
        subject = f"Invoice {invoice.get('invoice_number')} from {org.get('company_name', 'Our Company') if org else 'Our Company'}"
        
        # Create email body
        body = f"""
Dear {invoice.get('customer_name', 'Customer')},

Please find your invoice details below:

Invoice Number: {invoice.get('invoice_number')}
Invoice Date: {invoice.get('invoice_date')}
Due Date: {invoice.get('due_date')}

Amount: ₹{invoice.get('grand_total', 0):,.2f}
Payment Status: {invoice.get('payment_status', 'unpaid').upper()}
Balance Due: ₹{invoice.get('balance_amount', 0):,.2f}

You can view and download your invoice here:
{email_data.get('invoice_url', 'View in your account')}

Thank you for your business!

Best regards,
{org.get('company_name', 'Our Company') if org else 'Our Company'}
{org.get('email', '') if org else ''}
{org.get('phone', '') if org else ''}
"""
        
        # TODO: Implement actual email sending using SMTP
        # For now, return success with email details
        # In production, you would use smtplib or a service like SendGrid
        
        return {
            "status": "success", 
            "message": f"Invoice {invoice.get('invoice_number')} email prepared for {recipient_email}",
            "recipient": recipient_email,
            "subject": subject,
            "note": "Email functionality requires SMTP configuration. Email details prepared successfully."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending invoice email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send invoice email: {str(e)}"
        )

@router.post("/{invoice_id}/reminder")
async def send_payment_reminder(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Send payment reminder for unpaid/overdue invoices.
    """
    try:
        invoice = db["invoices"].find_one({
            "invoice_id": invoice_id, 
            "account_id": current_user.account_id
        })
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Validate invoice status
        if invoice.get('payment_status') == 'paid':
            raise HTTPException(
                status_code=400,
                detail="Cannot send reminder for paid invoices"
            )
        
        if invoice.get('status') == 'cancelled':
            raise HTTPException(
                status_code=400,
                detail="Cannot send reminder for cancelled invoices"
            )
        
        # Get customer email
        customer_email = invoice.get('customer_email', '')
        if not customer_email:
            raise HTTPException(
                status_code=400,
                detail="Customer email not found. Please add customer email address."
            )
        
        # Get organization details
        org = db["organizations"].find_one({"account_id": current_user.account_id})
        
        # Check if overdue
        due_date = invoice.get('due_date')
        is_overdue = False
        days_overdue = 0
        
        if due_date:
            from datetime import datetime, date
            if isinstance(due_date, str):
                due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00')).date()
            else:
                due_date_obj = due_date
            
            today = date.today()
            if due_date_obj < today:
                is_overdue = True
                days_overdue = (today - due_date_obj).days
        
        # Prepare reminder email
        subject = f"Payment Reminder: Invoice {invoice.get('invoice_number')}"
        if is_overdue:
            subject = f"URGENT: Overdue Payment - Invoice {invoice.get('invoice_number')}"
        
        urgency_message = ""
        if is_overdue:
            urgency_message = f"\n⚠️ URGENT: This invoice is {days_overdue} day(s) overdue.\n"
        
        body = f"""
Dear {invoice.get('customer_name', 'Customer')},

This is a friendly reminder about your pending invoice.
{urgency_message}
Invoice Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Invoice Number: {invoice.get('invoice_number')}
Invoice Date: {invoice.get('invoice_date')}
Due Date: {invoice.get('due_date')}

Total Amount: ₹{invoice.get('grand_total', 0):,.2f}
Amount Paid: ₹{invoice.get('amount_received', 0):,.2f}
Balance Due: ₹{invoice.get('balance_amount', 0):,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please arrange payment at your earliest convenience.

Payment Methods:
• Bank Transfer
• Credit Card
• Cash

For any questions or to discuss payment arrangements, please contact us.

Best regards,
{org.get('company_name', 'Our Company') if org else 'Our Company'}
{org.get('email', '') if org else ''}
{org.get('phone', '') if org else ''}
"""
        
        # TODO: Implement actual email sending
        # For now, return success with reminder details
        
        return {
            "status": "success",
            "message": f"Payment reminder for {invoice.get('invoice_number')} prepared for {customer_email}",
            "recipient": customer_email,
            "is_overdue": is_overdue,
            "days_overdue": days_overdue if is_overdue else 0,
            "balance_due": invoice.get('balance_amount', 0),
            "note": "Email functionality requires SMTP configuration. Reminder details prepared successfully."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending reminder: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send reminder: {str(e)}"
        )

@router.post("/{invoice_id}/duplicate")
async def duplicate_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Duplicate an existing invoice with stock validation.
    IMPORTANT: Validates stock availability but does NOT deduct stock.
    Stock will only be deducted when the duplicated invoice is finalized/saved.
    """
    try:
        # 1. Fetch source invoice
        source_invoice = db["invoices"].find_one({
            "invoice_id": invoice_id,
            "account_id": current_user.account_id
        })
        if not source_invoice:
            raise HTTPException(status_code=404, detail="Source invoice not found")

        # 2. Validate stock availability for all items
        stock_errors = []
        for item in source_invoice.get("items", []):
            item_doc = db["items"].find_one({
                "item_id": item.get("item_id"),
                "account_id": current_user.account_id
            })
            
            if not item_doc:
                stock_errors.append(f"Item '{item.get('item_name')}' not found in inventory")
                continue
            
            current_stock = item_doc.get("current_stock", 0)
            required_qty = item.get("qty", 0)
            
            if current_stock < required_qty:
                stock_errors.append(
                    f"Insufficient stock for '{item.get('item_name')}'. "
                    f"Available: {current_stock}, Required: {required_qty}"
                )
        
        # If any stock validation errors, return them
        if stock_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cannot duplicate invoice due to insufficient stock",
                    "errors": stock_errors
                }
            )

        # 3. Get next invoice number
        last_invoice = db["invoices"].find_one(
            {"account_id": current_user.account_id},
            sort=[("created_at", pymongo.DESCENDING)]
        )
        
        new_num = 1
        if last_invoice and "invoice_number" in last_invoice:
            try:
                parts = last_invoice["invoice_number"].split('-')
                if len(parts) > 1:
                    new_num = int(parts[1]) + 1
            except (ValueError, IndexError):
                new_num = db["invoices"].count_documents({"account_id": current_user.account_id}) + 1
        
        invoice_number = f"INV-{str(new_num).zfill(4)}"

        # 4. Create new invoice based on source
        new_invoice = source_invoice.copy()
        new_invoice.update({
            "invoice_id": str(uuid.uuid4()),
            "invoice_number": invoice_number,
            "invoice_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "payment_status": "unpaid",
            "amount_received": 0,
            "balance_amount": source_invoice.get("grand_total", 0),
            "status": "active"
        })
        
        # Remove MongoDB internal ID and quotation reference
        if "_id" in new_invoice:
            del new_invoice["_id"]
        if "quotation_id" in new_invoice:
            del new_invoice["quotation_id"]
        if "quotation_number" in new_invoice:
            del new_invoice["quotation_number"]
            
        # 5. Insert the duplicate (stock will be deducted when invoice is finalized)
        db["invoices"].insert_one(new_invoice)
        
        return {
            "status": "success",
            "message": "Invoice duplicated successfully",
            "new_invoice_id": new_invoice["invoice_id"],
            "invoice_number": invoice_number,
            "note": "Stock validated but not deducted. Complete the invoice to finalize stock changes."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error duplicating invoice: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to duplicate invoice: {str(e)}"
        )

@router.get("/stats")
def get_invoice_stats(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Get invoice statistics for dashboard
    """
    try:
        account_id = current_user.account_id
        
        # Get today's date range
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get this month's date range
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Total invoices count
        total_invoices = db["invoices"].count_documents({
            "account_id": account_id,
            "status": {"$ne": "cancelled"}
        })
        
        # Today's invoices
        today_invoices = list(db["invoices"].find({
            "account_id": account_id,
            "status": {"$ne": "cancelled"},
            "created_at": {"$gte": today_start, "$lte": today_end}
        }))
        
        # This month's invoices
        month_invoices = list(db["invoices"].find({
            "account_id": account_id,
            "status": {"$ne": "cancelled"},
            "created_at": {"$gte": month_start}
        }))
        
        # Calculate totals
        today_total = sum(inv.get("grand_total", 0) for inv in today_invoices)
        month_total = sum(inv.get("grand_total", 0) for inv in month_invoices)
        
        # Get pending amount
        pending_invoices = list(db["invoices"].find({
            "account_id": account_id,
            "status": {"$ne": "cancelled"},
            "payment_status": {"$in": ["unpaid", "partial"]}
        }))
        
        pending_amount = sum(inv.get("balance_amount", 0) for inv in pending_invoices)
        
        # Get invoice count by payment status
        unpaid_count = db["invoices"].count_documents({
            "account_id": account_id,
            "status": {"$ne": "cancelled"},
            "payment_status": "unpaid"
        })
        
        partial_count = db["invoices"].count_documents({
            "account_id": account_id,
            "status": {"$ne": "cancelled"},
            "payment_status": "partial"
        })
        
        paid_count = db["invoices"].count_documents({
            "account_id": account_id,
            "status": {"$ne": "cancelled"},
            "payment_status": "paid"
        })
        
        return {
            "total_invoices": total_invoices,
            "today_invoices": len(today_invoices),
            "today_total": today_total,
            "month_invoices": len(month_invoices),
            "month_total": month_total,
            "pending_amount": pending_amount,
            "payment_status_counts": {
                "unpaid": unpaid_count,
                "partial": partial_count,
                "paid": paid_count
            }
        }
        
    except Exception as e:
        print(f"Error getting invoice stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving invoice statistics"
        )