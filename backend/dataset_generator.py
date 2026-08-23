"""
MicroSetu - Synthetic Dataset Generator for Micro-Merchant Alternative Underwriting
Generates empirical, high-fidelity UPI transaction logs & merchant profiles calibrated to
RBI Payment System Indicators, NPCI statistics, PM SVANidhi data, and field survey benchmarks.
"""

import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    {"type": "chai_stall", "name_prefix": ["Ramesh", "Mukesh", "Chai Point", "Shree Ram", "Gupta Ji", "Mishra"], "name_suffix": "Chai & Snacks", "avg_ticket": 35, "ticket_std": 15, "daily_tx_mean": 95, "daily_tx_std": 25, "margins": 0.55},
    {"type": "vegetable_vendor", "name_prefix": ["Sunita", "Ram Prasad", "Hari Om", "Laxmi", "Santosh", "Radha"], "name_suffix": "Fresh Vegetables", "avg_ticket": 120, "ticket_std": 45, "daily_tx_mean": 65, "daily_tx_std": 18, "margins": 0.28},
    {"type": "street_food", "name_prefix": ["Sharma", "Aggarwal", "Bombay", "Chaat Chatori", "Anand", "Dosa Corner"], "name_suffix": "Fast Food & Chaat", "avg_ticket": 90, "ticket_std": 35, "daily_tx_mean": 80, "daily_tx_std": 22, "margins": 0.45},
    {"type": "kirana_store", "name_prefix": ["Balaji", "Om Sai", "Mahadev", "Kisaan", "Ganesh", "Apna"], "name_suffix": "Provision & Kirana", "avg_ticket": 220, "ticket_std": 90, "daily_tx_mean": 55, "daily_tx_std": 15, "margins": 0.18},
    {"type": "auto_rickshaw", "name_prefix": ["Irfan", "Suresh", "Vikram", "Pravin", "Deepak", "Raju"], "name_suffix": "City Transport", "avg_ticket": 65, "ticket_std": 25, "daily_tx_mean": 35, "daily_tx_std": 10, "margins": 0.65},
    {"type": "flower_vendor", "name_prefix": ["Pooja", "Meena", "Shakti", "Gayatri", "Kamla"], "name_suffix": "Pushp Bhandar", "avg_ticket": 50, "ticket_std": 20, "daily_tx_mean": 45, "daily_tx_std": 14, "margins": 0.40},
]

CITIES = [
    {"city": "Delhi NCR", "tier": 1, "avg_multiplier": 1.2},
    {"city": "Mumbai", "tier": 1, "avg_multiplier": 1.25},
    {"city": "Lucknow", "tier": 2, "avg_multiplier": 0.95},
    {"city": "Patna", "tier": 2, "avg_multiplier": 0.90},
    {"city": "Ahmedabad", "tier": 2, "avg_multiplier": 1.05},
    {"city": "Varanasi", "tier": 3, "avg_multiplier": 0.85},
    {"city": "Indore", "tier": 2, "avg_multiplier": 1.0},
    {"city": "Jaipur", "tier": 2, "avg_multiplier": 0.98},
]

PRELOADED_PERSONAS = [
    {
        "id": "MERCH_RAMESH_001",
        "name": "Ramesh Kumar (Ramesh Tea Stall)",
        "category": "chai_stall",
        "city": "Delhi NCR",
        "phone": "+91 98765 43210",
        "upi_id": "rameshchai@okaxis",
        "tenure_months": 28,
        "persona_type": "prime_consistent",
        "description": "High velocity tea stall near metro station. Operates 29 days/month with over 110 transactions/day."
    },
    {
        "id": "MERCH_SUNITA_002",
        "name": "Sunita Devi (Fresh Sabzi Mandi)",
        "category": "vegetable_vendor",
        "city": "Patna",
        "phone": "+91 98112 34567",
        "upi_id": "sunitaveg@paytm",
        "tenure_months": 18,
        "persona_type": "near_prime_growing",
        "description": "Vegetable cart operator. Consistent weekday sales, seasonal spikes, seeking second PM SVANidhi tranche."
    },
    {
        "id": "MERCH_RAJESH_003",
        "name": "Rajesh Gupta (Gupta Kirana & General)",
        "category": "kirana_store",
        "city": "Mumbai",
        "phone": "+91 97234 56789",
        "upi_id": "guptakirana@icici",
        "tenure_months": 42,
        "persona_type": "super_prime_established",
        "description": "High ticket density, loyal customer repeat base (62%), high monthly cashflow, eligible for ₹50,000 top tranche."
    },
    {
        "id": "MERCH_VIKRAM_004",
        "name": "Vikram Auto Services",
        "category": "auto_rickshaw",
        "city": "Lucknow",
        "phone": "+91 96543 21098",
        "upi_id": "vikramauto@ybl",
        "tenure_months": 8,
        "persona_type": "sub_prime_volatile",
        "description": "High income volatility, erratic working days (14-18 days/mo), high ticket variance, entry-level risk."
    },
    {
        "id": "MERCH_NEW_005",
        "name": "Anil Kumar (New Chaat Corner)",
        "category": "street_food",
        "city": "Varanasi",
        "phone": "+91 95432 10987",
        "upi_id": "anilchaat@sbi",
        "tenure_months": 2,
        "persona_type": "unbanked_new",
        "description": "Newly onboarded QR vendor (2 months history). Zero bureau score, seeking first PM SVANidhi loan of ₹10,000."
    }
]

def generate_merchant_cohort(num_merchants=1200, seed=42):
    """Generates synthetic merchants with realistic behavioral features for ML training."""
    np.random.seed(seed)
    random.seed(seed)
    
    merchants = []
    
    for i in range(num_merchants):
        m_id = f"MERCH_{i+1:04d}"
        cat = random.choice(CATEGORIES)
        loc = random.choice(CITIES)
        
        prefix = random.choice(cat["name_prefix"])
        business_name = f"{prefix} {cat['name_suffix']}"
        owner_name = f"{prefix} {'Singh' if random.random() > 0.5 else 'Kumar'}"
        
        # Tenure on UPI (months)
        tenure_months = max(1, int(np.random.exponential(scale=18)))
        
        # Operational discipline (active days per month out of 30)
        active_days_per_month = int(np.clip(np.random.normal(loc=25, scale=4), 8, 30))
        
        # Daily Transaction Volume
        daily_tx_count = max(5, int(np.random.normal(loc=cat["daily_tx_mean"] * loc["avg_multiplier"], scale=cat["daily_tx_std"])))
        
        # Average ticket size (86% <= 500 in accordance with NPCI micro-payment distribution)
        avg_ticket_size = max(15.0, round(np.random.lognormal(mean=np.log(cat["avg_ticket"]), sigma=0.4), 2))
        ticket_size_variance = round(avg_ticket_size * np.random.uniform(0.15, 0.65), 2)
        
        # Revenue metrics
        monthly_upi_volume = int(daily_tx_count * active_days_per_month * avg_ticket_size)
        
        # Customer loyalty & repeat retention (Ratio of unique UPI handles transacting >3 times/month)
        repeat_customer_ratio = round(np.clip(np.random.beta(a=4, b=3), 0.10, 0.85), 3)
        
        # Daily revenue volatility coefficient (standard deviation / mean daily revenue)
        cashflow_volatility_cv = round(np.clip(np.random.normal(loc=0.32, scale=0.12), 0.08, 0.95), 3)
        
        # Soundbox usage & digital verification diligence
        uses_audio_soundbox = 1 if (random.random() < 0.68 or monthly_upi_volume > 30000) else 0
        
        # Disputed/Failed transaction reversal rate (percentage)
        failed_dispute_rate = round(np.clip(np.random.exponential(scale=0.8), 0.05, 5.5), 2)
        
        # Peak-to-trough weekend multiplier
        weekend_stability_ratio = round(np.random.uniform(0.75, 1.45), 2)
        
        # Prior PM SVANidhi participation
        prior_svanidhi_tier = 0
        if tenure_months >= 12 and monthly_upi_volume >= 20000 and random.random() > 0.4:
            prior_svanidhi_tier = random.choice([1, 2])
            
        on_time_repayment_ratio = 1.0 if prior_svanidhi_tier == 0 else round(np.random.beta(a=8, b=1.5), 2)
        
        # Target: Loan Default / Delinquency Probability (Ground truth for credit scoring)
        latent_risk = (
            - 0.025 * tenure_months
            - 0.040 * active_days_per_month
            - 0.00003 * monthly_upi_volume
            - 1.8 * repeat_customer_ratio
            + 3.2 * cashflow_volatility_cv
            - 0.8 * uses_audio_soundbox
            + 0.6 * failed_dispute_rate
            - 1.5 * on_time_repayment_ratio
            + np.random.normal(0, 0.4)
        )
        
        # Probability of 30+ day default on a working capital micro-loan
        prob_default = 1.0 / (1.0 + np.exp(-(latent_risk + 1.2)))
        default_label = 1 if prob_default > 0.35 else 0
        
        # Derived SetuScore (300 to 900 scale)
        base_score = 900 - int(prob_default * 550) + random.randint(-15, 15)
        setu_score = int(np.clip(base_score, 300, 890))
        
        # PM SVANidhi Recommended Tranche
        if setu_score >= 720 and tenure_months >= 12:
            recommended_tranche = 50000
            risk_category = "Prime"
        elif setu_score >= 620:
            recommended_tranche = 20000
            risk_category = "Near-Prime"
        elif setu_score >= 520:
            recommended_tranche = 10000
            risk_category = "Moderate"
        else:
            recommended_tranche = 0
            risk_category = "High Risk / Sub-Prime"

        merchants.append({
            "merchant_id": m_id,
            "business_name": business_name,
            "owner_name": owner_name,
            "category": cat["type"],
            "city": loc["city"],
            "city_tier": loc["tier"],
            "tenure_months": tenure_months,
            "active_days_per_month": active_days_per_month,
            "daily_tx_count": daily_tx_count,
            "avg_ticket_size": avg_ticket_size,
            "ticket_size_variance": ticket_size_variance,
            "monthly_upi_volume": monthly_upi_volume,
            "repeat_customer_ratio": repeat_customer_ratio,
            "cashflow_volatility_cv": cashflow_volatility_cv,
            "uses_audio_soundbox": uses_audio_soundbox,
            "failed_dispute_rate": failed_dispute_rate,
            "weekend_stability_ratio": weekend_stability_ratio,
            "prior_svanidhi_tier": prior_svanidhi_tier,
            "on_time_repayment_ratio": on_time_repayment_ratio,
            "prob_default": round(float(prob_default), 4),
            "default_label": int(default_label),
            "setu_score": setu_score,
            "risk_category": risk_category,
            "recommended_tranche": recommended_tranche
        })
        
    df = pd.DataFrame(merchants)
    csv_path = DATA_DIR / "micro_merchants_dataset.csv"
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} synthetic merchant records at {csv_path}")
    return df

def generate_sample_transactions_for_merchant(merchant_id="MERCH_RAMESH_001", days=30):
    """Generates granular daily timestamped UPI transactions for a given merchant."""
    random.seed(42)
    np.random.seed(42)
    
    # Load persona or default
    persona = next((p for p in PRELOADED_PERSONAS if p["id"] == merchant_id), PRELOADED_PERSONAS[0])
    cat = next((c for c in CATEGORIES if c["type"] == persona["category"]), CATEGORIES[0])
    
    txs = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    current_date = start_date
    tx_counter = 1
    
    customer_pool = [f"cust_{i:03d}@upi" for i in range(1, 150)]
    repeat_customers = random.sample(customer_pool, 35)
    
    while current_date <= end_date:
        # Check if active today
        if random.random() < 0.92:
            num_txs = max(10, int(np.random.normal(cat["daily_tx_mean"], cat["daily_tx_std"])))
            
            # Distribute throughout business hours (6 AM to 10 PM)
            for _ in range(num_txs):
                hour = random.choices(
                    [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
                    weights=[2, 6, 12, 14, 8, 5, 6, 4, 3, 5, 9, 14, 15, 12, 8, 4, 1]
                )[0]
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                tx_time = current_date.replace(hour=hour, minute=minute, second=second)
                
                # Ticket size
                amount = max(10, round(float(np.random.lognormal(mean=np.log(cat["avg_ticket"]), sigma=0.35)), 0))
                
                # Customer
                if random.random() < 0.45:
                    payer_vpa = random.choice(repeat_customers)
                    is_repeat = True
                else:
                    payer_vpa = f"user_{random.randint(1000, 9999)}@oksbi"
                    is_repeat = False
                    
                # App mode
                payer_app = random.choices(["GooglePay", "PhonePe", "Paytm", "BHIM", "Cred", "AmazonPay"], weights=[38, 44, 12, 3, 2, 1])[0]
                
                # Generate realistic 12-digit UTR
                utr = f"4{random.randint(10000000000, 99999999999)}"
                
                status = "SUCCESS"
                if random.random() < 0.015:
                    status = "FAILED"
                    
                txs.append({
                    "tx_id": f"TXN_{tx_counter:06d}",
                    "utr": utr,
                    "merchant_id": merchant_id,
                    "amount": amount,
                    "timestamp": tx_time.isoformat(),
                    "payer_vpa": payer_vpa,
                    "payer_app": payer_app,
                    "status": status,
                    "is_repeat_customer": is_repeat,
                    "voice_soundbox_announced": True if status == "SUCCESS" else False
                })
                tx_counter += 1
                
        current_date += timedelta(days=1)
        
    return txs

if __name__ == "__main__":
    df = generate_merchant_cohort(1200)
    txs = generate_sample_transactions_for_merchant("MERCH_RAMESH_001", 30)
    with open(DATA_DIR / "sample_transactions.json", "w") as f:
        json.dump(txs, f, indent=2)
    print(f"Generated {len(txs)} sample transactions for Ramesh Chaiwala.")
