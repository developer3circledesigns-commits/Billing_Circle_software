import os
from flask import Flask

app = Flask(__name__, template_folder='app/frontend/templates')

with app.app_context():
    print("Files in app/frontend/templates/purchase_bills:")
    try:
        print(os.listdir('app/frontend/templates/purchase_bills'))
    except Exception as e:
        print(f"Error listing dir: {e}")

    print("\nAttempting to find 'purchase_bills/form.html':")
    template_path = 'purchase_bills/form.html'
    full_path = os.path.join('app/frontend/templates', template_path)
    print(f"Checking path: {full_path}")
    print(f"Exists: {os.path.exists(full_path)}")
