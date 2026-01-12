from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from datetime import datetime, timedelta
import io
import csv
import re

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(
    days: int = Query(7),
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Get dashboard statistics with optimized aggregation.
    Replaces daily loops with a single group-by-date pipeline.
    """
    account_id = current_user.account_id
    
    # 1. Parse custom date range
    date_filter = {}
    if start_date and end_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            date_filter = {"invoice_date": {"$gte": start_dt, "$lte": end_dt}}
        except:
            pass
    
    # 2. Financial Stats (Total Sales & Receivables)
    invoice_match = {"account_id": account_id, "status": "active"}
    if date_filter:
        invoice_match.update(date_filter)
    
    finance_pipeline = [
        {"$match": invoice_match},
        {"$group": {
            "_id": None,
            "total_sales": {"$sum": "$grand_total"},
            "total_receivables": {"$sum": "$balance_amount"}
        }}
    ]
    finance_stats = list(db["invoices"].aggregate(finance_pipeline))
    finance = finance_stats[0] if finance_stats else {"total_sales": 0, "total_receivables": 0}

    # 3. Total Payables (from Weavers)
    weaver_pipeline = [
        {"$match": {"account_id": account_id, "status": "active"}},
        {"$group": {"_id": None, "total_payables": {"$sum": "$current_balance"}}}
    ]
    payables_res = list(db["weavers"].aggregate(weaver_pipeline))
    total_payables = payables_res[0]["total_payables"] if payables_res else 0

    # 4. Inventory Value
    item_pipeline = [
        {"$match": {"account_id": account_id, "status": "active"}},
        {"$group": {"_id": None, "total_inventory_value": {"$sum": {"$multiply": ["$current_stock", "$purchase_price"]}}}}
    ]
    inventory_res = list(db["items"].aggregate(item_pipeline))
    inventory_value = inventory_res[0]["total_inventory_value"] if inventory_res else 0

    # 5. Low stock & Quotations
    low_stock_count = db["items"].count_documents({
        "account_id": account_id, 
        "status": "active",
        "$expr": {"$lte": ["$current_stock", "$reorder_level"]}
    })
    quote_pending = db["quotations"].count_documents({
        "account_id": account_id, 
        "status": {"$in": ["draft", "sent"]}
    })

    # 6. Optimized Revenue Chart Data (One Pipeline)
    history_cutoff = datetime.utcnow() - timedelta(days=days)
    chart_pipeline = [
        {"$match": {
            "account_id": account_id,
            "status": "active",
            "invoice_date": {"$gte": history_cutoff}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$invoice_date"},
                "month": {"$month": "$invoice_date"},
                "day": {"$dayOfMonth": "$invoice_date"}
            },
            "daily_total": {"$sum": "$grand_total"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
    ]
    chart_results = list(db["invoices"].aggregate(chart_pipeline))
    
    # Map results to contiguous days
    revenue_map = {f"{r['_id']['year']}-{r['_id']['month']}-{r['_id']['day']}": r['daily_total'] for r in chart_results}
    recent_revenue = []
    days_labels = []
    
    for i in range(days - 1, -1, -1):
        dt = datetime.utcnow() - timedelta(days=i)
        key = f"{dt.year}-{dt.month}-{dt.day}"
        recent_revenue.append(revenue_map.get(key, 0))
        days_labels.append(dt.strftime("%d %b") if days > 7 else dt.strftime("%a"))

    return {
        "total_sales": finance.get("total_sales", 0),
        "receivables": finance.get("total_receivables", 0),
        "payables": total_payables,
        "inventory_value": inventory_value,
        "low_stock_count": low_stock_count,
        "quote_pending": quote_pending,
        "recent_revenue": recent_revenue,
        "days_labels": days_labels
    }

@router.get("/activity")
def get_recent_activity(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    account_id = current_user.account_id
    activities = []

    # Get recent invoices
    invoices = list(db["invoices"].find({"account_id": account_id}).sort("created_at", -1).limit(5))
    for inv in invoices:
        activities.append({
            "type": "invoice",
            "title": f"Invoice {inv['invoice_number']}",
            "desc": f"₹{inv['grand_total']:.2f} for {inv['customer_name']}",
            "time": inv.get("created_at", datetime.utcnow()),
            "icon": "bi-receipt",
            "color": "success"
        })

    # Get recent items
    items = list(db["items"].find({"account_id": account_id}).sort("created_at", -1).limit(5))
    for item in items:
        activities.append({
            "type": "item",
            "title": "New Item Added",
            "desc": f"{item['item_name']} added to inventory",
            "time": item.get("created_at", datetime.utcnow()),
            "icon": "bi-box-seam",
            "color": "primary"
        })
        
    # Get recent weavers
    weavers = list(db["weavers"].find({"account_id": account_id}).sort("created_at", -1).limit(5))
    for w in weavers:
        activities.append({
            "type": "weaver",
            "title": "New Weaver Registered",
            "desc": f"{w['weaver_name']} added to masters",
            "time": w.get("created_at", datetime.utcnow()),
            "icon": "bi-person-plus",
            "color": "info"
        })

    # Sort all and take top 5
    activities.sort(key=lambda x: x["time"], reverse=True)
    return activities[:6]

@router.get("/report/summary")
def download_summary_report(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    stats = get_dashboard_stats(days=7, current_user=current_user, db=db)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Sales", f"INR {stats['total_sales']:.2f}"])
    writer.writerow(["Total Receivables", f"INR {stats['receivables']:.2f}"])
    writer.writerow(["Total Payables", f"INR {stats['payables']:.2f}"])
    writer.writerow(["Total Inventory Value", f"INR {stats['inventory_value']:.2f}"])
    writer.writerow(["Low Stock Items", stats['low_stock_count']])
    writer.writerow([])
    writer.writerow(["Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")])
    
    response = Response(content=output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=dashboard_summary.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

@router.get("/search")
def global_search(
    q: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Search across all major modules for the current account.
    Filters for active records only.
    """
    account_id = current_user.account_id
    results = []
    regex = re.compile(q, re.IGNORECASE)

    # 1. Search Customers (Active Only)
    customers = list(db["customers"].find({
        "account_id": account_id, 
        "status": {"$ne": "inactive"},
        "$or": [{"customer_name": regex}, {"customer_code": regex}]
    }).limit(3))
    for c in customers:
        results.append({"type": "Customer", "name": c["customer_name"], "url": f"/customers/view/{c['customer_id']}"})

    # 2. Search Items (Active Only)
    items = list(db["items"].find({
        "account_id": account_id, 
        "status": {"$ne": "inactive"},
        "item_name": regex
    }).limit(3))
    for i in items:
        results.append({"type": "Item", "name": i["item_name"], "url": f"/items/view/{i['item_id']}"})

    # 3. Search Invoices
    invoices = list(db["invoices"].find({
        "account_id": account_id, 
        "invoice_number": regex
    }).limit(3))
    for v in invoices:
        results.append({"type": "Invoice", "name": v["invoice_number"], "url": f"/invoices/view/{v['invoice_id']}"})

    # 4. Search Weavers (Active Only)
    weavers = list(db["weavers"].find({
        "account_id": account_id, 
        "status": {"$ne": "inactive"},
        "weaver_name": regex
    }).limit(3))
    for w in weavers:
        results.append({"type": "Weaver", "name": w["weaver_name"], "url": f"/weavers/view/{w['weaver_id']}"})

    # 5. Search Categories
    categories = list(db["categories"].find({
        "account_id": account_id, 
        "category_name": regex
    }).limit(3))
    for cat in categories:
        results.append({"type": "Category", "name": cat["category_name"], "url": "/categories"})

    # 6. Search Purchase Bills
    bills = list(db["purchase_bills"].find({
        "account_id": account_id, 
        "bill_number": regex
    }).limit(3))
    for b in bills:
        results.append({"type": "Purchase Bill", "name": b["bill_number"], "url": "/purchase-bills"})

    return results

@router.get("/notifications")
def get_notifications(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    account_id = current_user.account_id
    notifications = []

    # Low Stock Notification
    low_stock = list(db["items"].find({
        "account_id": account_id,
        "status": "active",
        "$expr": {"$lte": ["$current_stock", "$reorder_level"]}
    }))
    if low_stock:
        notifications.append({
            "id": "low_stock",
            "title": "Low Stock Alert",
            "message": f"{len(low_stock)} items are below reorder levels.",
            "type": "warning",
            "time": "Just now"
        })

    # Overdue Invoices Placeholder
    overdue = db["invoices"].count_documents({
        "account_id": account_id,
        "status": "active",
        "payment_status": {"$ne": "paid"},
        "due_date": {"$lt": datetime.utcnow()} # Assuming due_date exists
    })
    if overdue > 0:
        notifications.append({
            "id": "overdue",
            "title": "Overdue Invoices",
            "message": f"You have {overdue} overdue invoices pending payment.",
            "type": "danger",
            "time": "Today"
        })

    return notifications

@router.get("/top-selling-items")
def get_top_selling_items(
    limit: int = Query(5),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get top selling items by revenue"""
    account_id = current_user.account_id
    
    # Aggregate invoice items to find top sellers
    pipeline = [
        {"$match": {"account_id": account_id, "status": "active"}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.item_id",
            "item_name": {"$first": "$items.item_name"},
            "total_quantity": {"$sum": "$items.qty"},
            "total_revenue": {"$sum": "$items.total"}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": limit}
    ]
    
    top_items = list(db["invoices"].aggregate(pipeline))
    
    return [{
        "item_id": item["_id"],
        "item_name": item["item_name"],
        "total_quantity": item["total_quantity"],
        "total_revenue": item["total_revenue"]
    } for item in top_items]

@router.get("/recent-invoices")
def get_recent_invoices(
    limit: int = Query(10),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get recent invoices with status"""
    account_id = current_user.account_id
    
    invoices = list(db["invoices"].find(
        {"account_id": account_id, "status": "active"}
    ).sort("created_at", -1).limit(limit))
    
    result = []
    for inv in invoices:
        # Determine status based on payment and due date
        status = "paid"
        status_color = "success"
        
        if inv.get("payment_status") == "paid":
            status = "paid"
            status_color = "success"
        elif inv.get("due_date") and inv["due_date"] < datetime.utcnow():
            status = "overdue"
            status_color = "danger"
        else:
            status = "due"
            status_color = "warning"
        
        result.append({
            "invoice_id": inv.get("invoice_id"),
            "invoice_number": inv.get("invoice_number"),
            "customer_name": inv.get("customer_name"),
            "grand_total": inv.get("grand_total", 0),
            "balance_amount": inv.get("balance_amount", 0),
            "payment_status": inv.get("payment_status", "unpaid"),
            "status": status,
            "status_color": status_color,
            "due_date": inv.get("due_date").isoformat() if inv.get("due_date") else None,
            "invoice_date": inv.get("invoice_date").isoformat() if inv.get("invoice_date") else None
        })
    
    return result

@router.get("/calendar-events")
def get_calendar_events(
    month: int = Query(None),
    year: int = Query(None),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get invoice due dates for calendar view"""
    account_id = current_user.account_id
    
    # Default to current month if not specified
    now = datetime.utcnow()
    target_month = month if month else now.month
    target_year = year if year else now.year
    
    # Get start and end of month
    from calendar import monthrange
    _, last_day = monthrange(target_year, target_month)
    start_of_month = datetime(target_year, target_month, 1)
    end_of_month = datetime(target_year, target_month, last_day, 23, 59, 59)
    
    # Find invoices with due dates in this month
    invoices = list(db["invoices"].find({
        "account_id": account_id,
        "status": "active",
        "due_date": {"$gte": start_of_month, "$lte": end_of_month}
    }))
    
    # Group by date
    events_by_date = {}
    for inv in invoices:
        if inv.get("due_date"):
            date_key = inv["due_date"].strftime("%Y-%m-%d")
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            
            events_by_date[date_key].append({
                "invoice_id": inv.get("invoice_id"),
                "invoice_number": inv.get("invoice_number"),
                "customer_name": inv.get("customer_name"),
                "amount": inv.get("grand_total", 0),
                "payment_status": inv.get("payment_status", "unpaid")
            })
    
    return events_by_date

@router.get("/organization")
def get_organization_info(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Get organization/company information for branding and company switcher.
    Uses the organizations collection for accurate company details.
    """
    account_id = current_user.account_id
    
    # Get organization details
    org = db["organizations"].find_one({"account_id": account_id})
    
    # Fallback to account info if org is missing
    if not org:
        account = db["accounts"].find_one({"account_id": account_id})
        return {
            "account_id": account_id,
            "company_name": account.get("company_name", "My Company") if account else "My Company",
            "plan": account.get("subscription_type", "free") if account else "free"
        }
    
    # Get account details for plan
    account = db["accounts"].find_one({"account_id": account_id})
    plan = account.get("subscription_type", "free") if account else "free"
    
    return {
        "account_id": account_id,
        "company_name": org.get("company_name", "My Company"),
        "address": org.get("address", ""),
        "gstin": org.get("gstin", ""),
        "email": org.get("email", ""),
        "plan": plan
    }
