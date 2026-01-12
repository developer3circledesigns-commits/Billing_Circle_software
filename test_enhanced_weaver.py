import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_enhanced_weaver():
    # 1. Login
    login_resp = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@billing.com", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Weaver with all fields
    weaver_data = {
        "weaver_name": "Premium Textiles Ltd",
        "display_name": "Premium Tex",
        "contact_number": "9988776655",
        "email": "contact@premiumtex.com",
        "address": "123 Industrial Hub, Surat, Gujarat",
        "gstin": "24AAAAA0000A1Z5",
        "pan_number": "AAAAA0000A",
        "bank_name": "HDFC Bank",
        "account_name": "Premium Textiles Ltd",
        "account_number": "50100012345678",
        "ifsc_code": "HDFC0001234",
        "opening_balance": 50000.0,
        "cost": 150.0,
        "credit_period_days": 30,
        "payment_terms": "net_30",
        "notes": "Reliable supplier for silk yarns."
    }
    
    print("Creating enhanced weaver...")
    create_resp = requests.post(f"{BASE_URL}/weavers/", json=weaver_data, headers=headers)
    if create_resp.status_code == 200:
        weaver = create_resp.json()
        print(f"SUCCESS: Weaver {weaver['weaver_code']} created.")
        
        # Verify current_balance == opening_balance
        if weaver["current_balance"] == 50000.0:
            print("VERIFIED: current_balance correctly initialized.")
        else:
            print(f"FAILURE: current_balance is {weaver['current_balance']}, expected 50000.0")
            
        # Verify banking fields
        if weaver["bank_name"] == "HDFC Bank":
            print("VERIFIED: Bank details persisted.")
        else:
            print("FAILURE: Bank details missing.")
    else:
        print(f"FAILURE: Status {create_resp.status_code}, Detail: {create_resp.text}")

if __name__ == "__main__":
    test_enhanced_weaver()
