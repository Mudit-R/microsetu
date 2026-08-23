"""
MicroSetu - Vernacular Voice & Natural Language Ledger Parser
Parses unstructured Hindi, Hinglish, and English voice/text speech inputs into
structured accounting entries (Income/Expense/Category/Amount) for micro-merchants.
"""

import re
from datetime import datetime

# Regex and semantic mappings for vernacular Indian street commerce
EXPENSE_KEYWORDS = [
    "kharidi", "kharida", "liye", "diye", "kharcha", "payment kiya", "bhugtan", 
    "bought", "purchase", "paid", "expense", "spent", "kharch", "laaye", "lagaya",
    "sabzi", "doodh", "chai", "cheeni", "oil", "tel", "cylinder", "gas", "kiraya", "rent",
    "advance", "helper", "wages", "mazdoori"
]

INCOME_KEYWORDS = [
    "mile", "aaye", "aaya", "prapt", "received", "earned", "kamaya", "bikri", 
    "sale", "customer", "bika", "becha", "cash mila", "paytm", "gpay", "phonepe", "upi"
]

CATEGORY_RULES = [
    {"category": "Dairy & Milk", "keywords": ["doodh", "milk", "paneer", "dahi", "amul"]},
    {"category": "Vegetables & Produce", "keywords": ["sabzi", "tamatar", "pyaaz", "aloo", "vegetable", "mandi"]},
    {"category": "Tea, Sugar & Dry Provisions", "keywords": ["chai", "tea", "cheeni", "sugar", "patti", "masala", "kirana"]},
    {"category": "Fuel & Utilities", "keywords": ["gas", "cylinder", "bijli", "electricity", "fuel", "petrol", "diesel"]},
    {"category": "Rent & Stall Fee", "keywords": ["kiraya", "rent", "dukan", "stall fee", "nagar nigam"]},
    {"category": "Wages & Labor", "keywords": ["mazdoori", "helper", "raju", "salary", "advance", "chhotu"]},
    {"category": "Customer Digital Sales", "keywords": ["phonepe", "gpay", "paytm", "upi", "online", "qr"]},
    {"category": "Cash Sales", "keywords": ["cash", "rokda", "nagad", "haath me"]}
]

HINDI_NUMERAL_WORDS = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5, "chhah": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "sau": 100, "hazar": 1000, "hazaar": 1000, "dedh sau": 150, "dhai sau": 250, "pachas": 50, "so": 100
}

def parse_vernacular_ledger_entry(text: str) -> dict:
    """
    Parses a spoken or typed vernacular sentence into a structured ledger entry.
    Example: "Aaj 450 rupaye ki sabzi kharidi mandi se"
    """
    if not text:
        return {"success": False, "error": "Empty speech transcript."}
        
    cleaned = text.lower().strip()
    
    # 1. Extract Amount (Digits or Currency symbols)
    # Match patterns like: ₹450, 450rs, 450 rs, 450 rupaye, 450/-
    amount = 0.0
    amount_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rs|rupaye|rupees|rupya|/-)?', cleaned)
    if amount_match:
        amount_str = amount_match.group(1).replace(",", "")
        try:
            amount = float(amount_str)
        except ValueError:
            amount = 0.0
            
    # 2. Determine Transaction Type (Income vs Expense)
    tx_type = "EXPENSE"  # Default assumption for manual vendor logging is tracking costs
    is_income = any(k in cleaned for k in INCOME_KEYWORDS)
    is_expense = any(k in cleaned for k in EXPENSE_KEYWORDS)
    
    if is_income and not is_expense:
        tx_type = "INCOME"
    elif is_expense:
        tx_type = "EXPENSE"
    elif "sale" in cleaned or "bikri" in cleaned or "mile" in cleaned:
        tx_type = "INCOME"

    # 3. Categorize
    detected_category = "General / Miscellaneous"
    for rule in CATEGORY_RULES:
        if any(k in cleaned for k in rule["keywords"]):
            detected_category = rule["category"]
            break
            
    if tx_type == "INCOME" and detected_category == "General / Miscellaneous":
        detected_category = "Daily Sales Revenue"

    # 4. Generate clean description
    clean_desc = text.strip()
    
    return {
        "success": True,
        "raw_text": text,
        "entry_type": tx_type,
        "amount": amount,
        "category": detected_category,
        "description": clean_desc,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.94 if amount > 0 else 0.60,
        "formatted_announcement": f"₹{amount:,.0f} logged as {detected_category} ({tx_type})"
    }

if __name__ == "__main__":
    tests = [
        "Aaj ₹450 ki sabzi kharidi mandi se",
        "Paytm pe 120 rupaye customer se mile",
        "Amul doodh 3 packet 180 rs",
        "Cash sales total 1500 rupaye",
        "Gas cylinder refill 1100 diya"
    ]
    for t in tests:
        res = parse_vernacular_ledger_entry(t)
        print(f"Input: '{t}' -> Type: {res['entry_type']}, Amount: ₹{res['amount']}, Cat: {res['category']}")
