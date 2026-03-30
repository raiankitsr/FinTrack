import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

# ── 12 months of daily transactions ──────────────────────────────────────────
start_date = datetime(2024, 1, 1)
end_date   = datetime(2024, 12, 31)

categories = {
    "Income":        {"subcats": ["Salary", "Freelance", "Dividends"], "type": "income"},
    "Housing":       {"subcats": ["Rent", "Electricity", "Internet", "Maintenance"], "type": "expense"},
    "Food":          {"subcats": ["Groceries", "Restaurants", "Coffee", "Food Delivery"], "type": "expense"},
    "Transport":     {"subcats": ["Fuel", "Uber", "Metro", "Car Maintenance"], "type": "expense"},
    "Entertainment": {"subcats": ["OTT Subscriptions", "Movies", "Gaming", "Events"], "type": "expense"},
    "Health":        {"subcats": ["Gym", "Medicine", "Doctor", "Insurance"], "type": "expense"},
    "Shopping":      {"subcats": ["Clothing", "Electronics", "Home Decor", "Books"], "type": "expense"},
    "Investment":    {"subcats": ["Stocks", "Mutual Funds", "Crypto", "Gold"], "type": "expense"},
    "Savings":       {"subcats": ["Emergency Fund", "Fixed Deposit"], "type": "expense"},
}

amount_ranges = {
    "Salary":          (55000, 65000), "Freelance":       (5000, 20000),
    "Dividends":       (500,   3000),  "Rent":            (15000, 15000),
    "Electricity":     (800,   2000),  "Internet":        (699,   699),
    "Maintenance":     (500,   3000),  "Groceries":       (2000,  5000),
    "Restaurants":     (500,   3000),  "Coffee":          (200,   800),
    "Food Delivery":   (300,   1500),  "Fuel":            (1500,  3000),
    "Uber":            (200,   1000),  "Metro":           (100,   500),
    "Car Maintenance": (500,   5000),  "OTT Subscriptions":(500,  1500),
    "Movies":          (300,   800),   "Gaming":          (200,   2000),
    "Events":          (500,   3000),  "Gym":             (1500,  2500),
    "Medicine":        (200,   2000),  "Doctor":          (500,   3000),
    "Insurance":       (2000,  5000),  "Clothing":        (1000,  5000),
    "Electronics":     (2000, 15000),  "Home Decor":      (500,   5000),
    "Books":           (200,   1000),  "Stocks":          (3000, 10000),
    "Mutual Funds":    (2000,  8000),  "Crypto":          (1000,  5000),
    "Gold":            (1000,  5000),  "Emergency Fund":  (2000,  5000),
    "Fixed Deposit":   (5000, 20000),
}

frequency = {
    "Salary": "monthly", "Rent": "monthly", "Internet": "monthly",
    "Insurance": "quarterly", "Fixed Deposit": "quarterly",
    "Gym": "monthly", "OTT Subscriptions": "monthly",
    "Groceries": "weekly", "Fuel": "weekly",
    "Restaurants": "2x_week", "Coffee": "3x_week",
    "Food Delivery": "2x_week", "Uber": "weekly",
    "Metro": "daily_ish",
}

records = []

def should_include(subcat, date):
    freq = frequency.get(subcat, "random")
    d = date.weekday()
    if freq == "monthly":   return date.day in [1, 2, 3]
    if freq == "quarterly": return date.day in [1, 2] and date.month in [1, 4, 7, 10]
    if freq == "weekly":    return d == 0
    if freq == "2x_week":   return d in [1, 4]
    if freq == "3x_week":   return d in [0, 2, 5]
    if freq == "daily_ish": return random.random() < 0.6
    return random.random() < 0.15

current = start_date
while current <= end_date:
    for cat, info in categories.items():
        for subcat in info["subcats"]:
            if should_include(subcat, current):
                lo, hi = amount_ranges.get(subcat, (100, 1000))
                amt = round(random.uniform(lo, hi), 2)
                records.append({
                    "date":        current.strftime("%Y-%m-%d"),
                    "category":    cat,
                    "subcategory": subcat,
                    "amount":      amt,
                    "type":        info["type"],
                    "description": f"{subcat} payment",
                    "month":       current.strftime("%B"),
                    "month_num":   current.month,
                    "year":        current.year,
                })
    current += timedelta(days=1)

df = pd.DataFrame(records)
df.to_csv("transactions.csv", index=False)
print(f"Generated {len(df)} transactions")
print(df.groupby("type")["amount"].sum().round(2))
