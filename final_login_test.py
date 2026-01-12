import requests

login_data = {
    "username": "admin@billing.com",
    "password": "admin123"
}

try:
    response = requests.post("http://127.0.0.1:8000/api/v1/auth/login", data=login_data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Login Successful!")
        print(f"Token: {response.json().get('access_token')[:20]}...")
    else:
        print(f"Login Failed: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
