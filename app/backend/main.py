from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware to allow Flask frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the Flask app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_client():
    db.connect()
    from app.core.init_db import ensure_admin_exists
    ensure_admin_exists()

@app.on_event("shutdown")
def shutdown_db_client():
    db.close()

from app.backend.routers import (
    auth, users, weavers, customers, categories, items, dashboard, 
    quotations, invoices, payments, purchase_orders, purchase_bills, vendor_payments,
    subscriptions
)
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(weavers.router, prefix=f"{settings.API_V1_STR}/weavers", tags=["weavers"])
app.include_router(customers.router, prefix=f"{settings.API_V1_STR}/customers", tags=["customers"])
app.include_router(categories.router, prefix=f"{settings.API_V1_STR}/categories", tags=["categories"])
app.include_router(items.router, prefix=f"{settings.API_V1_STR}/items", tags=["items"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(quotations.router, prefix=f"{settings.API_V1_STR}/quotations", tags=["quotations"])
app.include_router(invoices.router, prefix=f"{settings.API_V1_STR}/invoices", tags=["invoices"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])

# Purchase Management Routers
app.include_router(purchase_orders.router, prefix=f"{settings.API_V1_STR}/purchase-orders", tags=["purchase-orders"])
app.include_router(purchase_bills.router, prefix=f"{settings.API_V1_STR}/purchase-bills", tags=["purchase-bills"])
app.include_router(vendor_payments.router, prefix=f"{settings.API_V1_STR}/vendor-payments", tags=["vendor-payments"])
app.include_router(subscriptions.router, prefix=f"{settings.API_V1_STR}/subscriptions", tags=["subscriptions"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Billing SaaS API"}

# Include routers here later
# from app.backend.routers import auth, users
# app.include_router(auth.router, prefix=settings.API_V1_STR)
