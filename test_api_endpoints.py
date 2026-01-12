import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_login():
    print("Testing Login...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data={
            "username": "admin@billing.com",
            "password": "admin123"
        })
        if resp.status_code == 200:
            print("Login successful.")
            return resp.json()["access_token"]
        else:
            print(f"Login failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None

def test_endpoint(endpoint, token):
    print(f"Testing {endpoint}...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        if resp.status_code == 200:
            print(f"SUCCESS: {endpoint} returned valid JSON.")
            # Verify no ObjectId is in the keys of the first item
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                if "_id" in data[0] and isinstance(data[0]["_id"], dict):
                     print(f"WARNING: Found raw _id in {endpoint}")
                else:
                     print(f"Verified: No raw _id in first item of {endpoint}")
            elif isinstance(data, dict):
                if "_id" in data and isinstance(data["_id"], dict):
                     print(f"WARNING: Found raw _id in {endpoint}")
            return True
        else:
            print(f"FAILED: {endpoint} returned {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"Error testing {endpoint}: {e}")
        return False

if __name__ == "__main__":
    token = test_login()
    if token:
        test_endpoint("/dashboard/stats", token)
        test_endpoint("/items/", token)
        test_endpoint("/customers/", token)
        test_endpoint("/weavers/", token)
        test_endpoint("/categories/", token)
        test_endpoint("/invoices/", token)
        test_endpoint("/quotations/", token)
        test_endpoint("/payments/", token)
        test_endpoint("/users/me", token)
