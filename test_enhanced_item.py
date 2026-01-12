import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_enhanced_item():
    # 1. Login
    login_resp = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@billing.com", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get Categories or Create one
    cat_resp = requests.get(f"{BASE_URL}/categories/", headers=headers)
    categories = cat_resp.json()
    if not categories:
        print("Creating placeholder category...")
        cat_data = {"category_name": "Silk Sarees", "description": "Traditional hand-woven silks"}
        cat_resp = requests.post(f"{BASE_URL}/categories/", json=cat_data, headers=headers)
        cat_id = cat_resp.json()["category_id"]
    else:
        cat_id = categories[0]["category_id"]

    # 3. Create Item with all fields
    item_data = {
        "item_name": "Premium Silk Saree",
        "item_type": "goods",
        "sku": "SILK-001",
        "brand": "Kanchipuram Heritage",
        "category_id": cat_id,
        "hsn_code": "5007",
        "unit": "PCS",
        "tax_preference": "taxable",
        "tax_rate": 5.0,
        "purchase_price": 4500.0,
        "selling_price": 7500.0,
        "opening_stock": 50.0,
        "opening_stock_rate": 4500.0,
        "reorder_level": 10,
        "description": "Hand-woven pure silk saree with gold zari work.",
        "notes": "Handle with care. Store in cool place."
    }
    
    print("Creating enhanced item...")
    create_resp = requests.post(f"{BASE_URL}/items/", json=item_data, headers=headers)
    if create_resp.status_code == 200:
        item = create_resp.json()
        print(f"SUCCESS: Item {item['item_id']} created.")
        
        # Verify current_stock == opening_stock
        if item["current_stock"] == 50.0:
            print("VERIFIED: current_stock correctly initialized.")
        else:
            print(f"FAILURE: current_stock is {item['current_stock']}, expected 50.0")
            
        # Verify brand field
        if item["brand"] == "Kanchipuram Heritage":
            print("VERIFIED: Brand field persisted.")
        else:
            print(f"FAILURE: Brand field missing or incorrect.")
    else:
        print(f"FAILURE: Status {create_resp.status_code}, Detail: {create_resp.text}")

if __name__ == "__main__":
    test_enhanced_item()
