
from app.backend.models.customer import CustomerCreate
import datetime

# Simulate a full enhanced customer payload
payload = {
    "customer_type": "business",
    "salutation": "Mr.",
    "first_name": "Test",
    "last_name": "User",
    "customer_name": "Test User",
    "display_name": "Test Company Pvt Ltd",
    "company_name": "Test Company Pvt Ltd",
    "contact_number": "9876543210",
    "mobile_number": "1234567890",
    "email": "test@example.com",
    "website": "http://example.com",
    "gstin": "22AAAAA0000A1Z5",
    "pan_number": "ABCDE1234F",
    "currency": "USD",
    "payment_terms": "net_30",
    "enable_portal": True,
    "billing_address": "123 St",
    "billing_city": "City",
    "billing_country": "India"
}

try:
    c = CustomerCreate(**payload)
    print("CustomerCreate model validated successfully!")
    print(c.dict())
except Exception as e:
    print(f"Validation Error: {e}")
