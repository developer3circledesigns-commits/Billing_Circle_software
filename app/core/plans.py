
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free Trial",
        "price": 0,
        "limits": {
            "invoices": 5,
            "quotations": 10,
            "items": 10,
            "users": 1,
            "reports": False
        },
        "features": ["Basic Invoicing", "Inventory Management", "Single User Access"]
    },
    "pro": {
        "name": "Professional",
        "price": 29,
        "limits": {
            "invoices": 1000,
            "quotations": 2000,
            "items": 5000,
            "users": 5,
            "reports": True
        },
        "features": ["Bulk Invoicing", "Advanced Reports", "Multi-user Access", "Priority Support"]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 99,
        "limits": {
            "invoices": -1, # Unlimited
            "quotations": -1, # Unlimited
            "items": -1, # Unlimited
            "users": -1, # Unlimited
            "reports": True
        },
        "features": ["Unlimited Everything", "Dedicated Account Manager", "Custom Integrations", "24/7 Phone Support"]
    }
}
