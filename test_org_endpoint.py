import requests

API_URL = "http://127.0.0.1:8000/api/v1"

def login():
    resp = requests.post(f"{API_URL}/auth/login", json={"email": "admin@billing.com", "password": "admin123"})
    return resp.json()["access_token"]

def test_org():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/dashboard/organization", headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Content: {resp.json()}")

if __name__ == "__main__":
    test_org()
