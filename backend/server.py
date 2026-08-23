"""
MicroSetu - Production FastAPI Backend & Intelligence Server
Serves REST APIs, Underwriting Engine, Fraud Detection Shield, Cashflow Analytics,
Voice Ledger Parser, and the Interactive Web Application.
"""

import os
import json
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

try:
    from .dataset_generator import (
        generate_merchant_cohort,
        generate_sample_transactions_for_merchant,
        PRELOADED_PERSONAS,
        CATEGORIES,
        CITIES,
        DATA_DIR
    )
    from .credit_model import get_underwriter, FEATURE_COLUMNS, FEATURE_DISPLAY_NAMES
    from .fraud_detector import get_fraud_shield
    from .cashflow_forecaster import forecast_merchant_cashflow
    from .voice_processor import parse_vernacular_ledger_entry
except ImportError:
    from dataset_generator import (
        generate_merchant_cohort,
        generate_sample_transactions_for_merchant,
        PRELOADED_PERSONAS,
        CATEGORIES,
        CITIES,
        DATA_DIR
    )
    from credit_model import get_underwriter, FEATURE_COLUMNS, FEATURE_DISPLAY_NAMES
    from fraud_detector import get_fraud_shield
    from cashflow_forecaster import forecast_merchant_cashflow
    from voice_processor import parse_vernacular_ledger_entry

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="MicroSetu FinTech Intelligence Engine",
    description="AI-Driven Alternative Credit Underwriting & Smart Vernacular POS for Informal Micro-Merchants",
    version="2.0.0"
)

# Enable CORS for external dev servers or local embedding
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session state for live demo and dynamic transactions
LIVE_MERCHANTS_STATE = {}
LIVE_LEDGER_STATE = {}

def init_state():
    for p in PRELOADED_PERSONAS:
        m_id = p["id"]
        sample_txs = generate_sample_transactions_for_merchant(m_id, days=30)
        
        # Calculate merchant aggregates
        total_vol = sum(t["amount"] for t in sample_txs if t["status"] == "SUCCESS")
        tx_count = len([t for t in sample_txs if t["status"] == "SUCCESS"])
        avg_ticket = total_vol / tx_count if tx_count > 0 else 50.0
        
        features = {
            "tenure_months": p["tenure_months"],
            "active_days_per_month": 28 if "prime" in p["persona_type"] else (22 if "near_prime" in p["persona_type"] else 16),
            "daily_tx_count": int(tx_count / 30) if tx_count > 0 else 40,
            "avg_ticket_size": round(avg_ticket, 2),
            "ticket_size_variance": round(avg_ticket * 0.35, 2),
            "monthly_upi_volume": int(total_vol),
            "repeat_customer_ratio": 0.58 if "prime" in p["persona_type"] else 0.32,
            "cashflow_volatility_cv": 0.18 if "prime" in p["persona_type"] else 0.48,
            "uses_audio_soundbox": 1,
            "failed_dispute_rate": 0.35,
            "weekend_stability_ratio": 1.15,
            "prior_svanidhi_tier": 2 if "super_prime" in p["persona_type"] else (1 if "near_prime" in p["persona_type"] else 0),
            "on_time_repayment_ratio": 0.98 if "prime" in p["persona_type"] else 0.85
        }
        
        uw = get_underwriter()
        eval_result = uw.evaluate_merchant(features)
        
        LIVE_MERCHANTS_STATE[m_id] = {
            "profile": p,
            "features": features,
            "underwriting": eval_result,
            "recent_transactions": sample_txs[-25:], # Keep last 25 for quick UI rendering
            "total_lifetime_txs": len(sample_txs),
            "created_at": datetime.now().isoformat()
        }
        
        # Initial dummy ledger records
        LIVE_LEDGER_STATE[m_id] = [
            {"id": "LED_001", "type": "EXPENSE", "amount": 420.0, "category": "Dairy & Milk", "description": "Amul milk 7 litres", "timestamp": (datetime.now() - timedelta(hours=8)).isoformat()},
            {"id": "LED_002", "type": "EXPENSE", "amount": 310.0, "category": "Tea, Sugar & Dry Provisions", "description": "Tea leaves & Ginger", "timestamp": (datetime.now() - timedelta(hours=6)).isoformat()},
            {"id": "LED_003", "type": "INCOME", "amount": 950.0, "category": "Customer Digital Sales", "description": "Morning tea burst payments (UPI)", "timestamp": (datetime.now() - timedelta(hours=4)).isoformat()},
            {"id": "LED_004", "type": "INCOME", "amount": 400.0, "category": "Cash Sales", "description": "Cash collections", "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()},
        ]

init_state()

# --- Request / Response Models ---

class UnderwriteRequest(BaseModel):
    merchant_id: Optional[str] = None
    tenure_months: float = Field(..., ge=1, le=120)
    active_days_per_month: float = Field(..., ge=1, le=31)
    daily_tx_count: float = Field(..., ge=1, le=1000)
    avg_ticket_size: float = Field(..., ge=5, le=50000)
    ticket_size_variance: Optional[float] = 15.0
    monthly_upi_volume: float = Field(..., ge=100)
    repeat_customer_ratio: float = Field(..., ge=0.0, le=1.0)
    cashflow_volatility_cv: float = Field(..., ge=0.0, le=2.0)
    uses_audio_soundbox: int = Field(..., ge=0, le=1)
    failed_dispute_rate: float = Field(..., ge=0.0, le=20.0)
    weekend_stability_ratio: Optional[float] = 1.1
    prior_svanidhi_tier: int = Field(0, ge=0, le=3)
    on_time_repayment_ratio: float = Field(1.0, ge=0.0, le=1.0)

class FraudCheckRequest(BaseModel):
    utr: str
    amount: float
    merchant_vpa: str
    timestamp_str: Optional[str] = None
    payer_vpa: Optional[str] = "user@upi"
    app_reported: Optional[str] = "PhonePe"
    screenshot_metadata: Optional[Dict[str, Any]] = None

class VoiceLedgerRequest(BaseModel):
    merchant_id: str
    text_transcript: str

class BurstSimulationRequest(BaseModel):
    merchant_id: str
    num_transactions: int = Field(10, ge=1, le=50)
    inject_fraud: bool = False

# --- REST Endpoints ---

@app.get("/health")
@app.get("/api/health")
def health_check():
    uw = get_underwriter()
    return {
        "status": "HEALTHY",
        "service": "MicroSetu FinTech Intelligence Engine",
        "timestamp": datetime.now().isoformat(),
        "model_metadata": uw.metadata,
        "active_merchants_in_memory": len(LIVE_MERCHANTS_STATE)
    }

@app.get("/api/merchants")
def list_merchants():
    """Returns preloaded vendor personas and live states."""
    result = []
    for m_id, data in LIVE_MERCHANTS_STATE.items():
        result.append({
            "merchant_id": m_id,
            "profile": data["profile"],
            "features": data["features"],
            "setu_score": data["underwriting"]["setu_score"],
            "risk_tier": data["underwriting"]["risk_tier"],
            "approved_limit": data["underwriting"]["approved_credit_limit"],
            "svanidhi_tranche": data["underwriting"]["svanidhi_tranche"]
        })
    return {"merchants": result}

@app.get("/api/merchants/{merchant_id}")
def get_merchant_details(merchant_id: str):
    """Retrieves full profile, scoring breakdown, cash flow, and recent ledger for a merchant."""
    if merchant_id not in LIVE_MERCHANTS_STATE:
        raise HTTPException(status_code=404, detail="Merchant not found")
        
    m_data = LIVE_MERCHANTS_STATE[merchant_id]
    ledger = LIVE_LEDGER_STATE.get(merchant_id, [])
    
    # Calculate ledger summary
    total_income = sum(item["amount"] for item in ledger if item["type"] == "INCOME")
    total_expense = sum(item["amount"] for item in ledger if item["type"] == "EXPENSE")
    net_profit = total_income - total_expense
    
    # Generate 30d forecast
    base_daily = (m_data["features"]["monthly_upi_volume"] / 30)
    forecast = forecast_merchant_cashflow(base_daily_revenue=base_daily)
    
    return {
        "profile": m_data["profile"],
        "features": m_data["features"],
        "underwriting": m_data["underwriting"],
        "recent_transactions": m_data["recent_transactions"],
        "ledger": {
            "entries": ledger,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": net_profit
        },
        "cashflow_forecast": forecast
    }

@app.post("/api/underwrite")
def underwrite_merchant(req: UnderwriteRequest):
    """Executes live ML credit scoring and generates explainable creditworthiness metrics."""
    uw = get_underwriter()
    features = req.model_dump()
    result = uw.evaluate_merchant(features)
    
    # If merchant_id is provided, update state
    if req.merchant_id and req.merchant_id in LIVE_MERCHANTS_STATE:
        LIVE_MERCHANTS_STATE[req.merchant_id]["features"] = features
        LIVE_MERCHANTS_STATE[req.merchant_id]["underwriting"] = result
        
    return result

@app.post("/api/fraud-check")
def check_payment_fraud(req: FraudCheckRequest):
    """Checks a payment claim / QR transaction for spoofing, replay attacks, or counterfeit APK signatures."""
    shield = get_fraud_shield()
    payload = req.model_dump()
    result = shield.verify_payment_claim(payload)
    return result

@app.post("/api/voice-ledger/parse")
def parse_voice_ledger(req: VoiceLedgerRequest):
    """Parses spoken natural language Hinglish/Hindi text and adds a verified entry to the merchant's ledger."""
    res = parse_vernacular_ledger_entry(req.text_transcript)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to parse text"))
        
    m_id = req.merchant_id
    new_entry = {
        "id": f"LED_{random.randint(1000, 9999)}",
        "type": res["entry_type"],
        "amount": res["amount"],
        "category": res["category"],
        "description": res["description"],
        "timestamp": res["timestamp"]
    }
    
    if m_id in LIVE_LEDGER_STATE:
        LIVE_LEDGER_STATE[m_id].insert(0, new_entry)
        
    return {
        "parsed_data": res,
        "entry": new_entry,
        "updated_ledger_count": len(LIVE_LEDGER_STATE.get(m_id, []))
    }

@app.get("/api/cashflow/forecast")
def get_cashflow_forecast(base_daily_revenue: float = 3500.0, horizon_days: int = 30):
    """Generates probabilistic revenue forecast and liquidity runway."""
    return forecast_merchant_cashflow(base_daily_revenue=base_daily_revenue, horizon_days=horizon_days)

@app.post("/api/simulate/burst")
def simulate_transaction_burst(req: BurstSimulationRequest):
    """
    Simulates high-traffic live payment bursts (e.g. morning rush at tea stall)
    to demonstrate real-time soundbox audio triggering and dynamic credit scoring.
    """
    m_id = req.merchant_id
    if m_id not in LIVE_MERCHANTS_STATE:
        m_id = "MERCH_RAMESH_001"
        
    m_data = LIVE_MERCHANTS_STATE[m_id]
    cat_type = m_data["profile"]["category"]
    cat = next((c for c in CATEGORIES if c["type"] == cat_type), CATEGORIES[0])
    
    generated_txs = []
    total_added_volume = 0
    
    shield = get_fraud_shield()
    
    for i in range(req.num_transactions):
        # Ticket
        amt = max(10, round(float(random.gauss(cat["avg_ticket"], cat["ticket_std"])), 0))
        utr = f"4{random.randint(10000000000, 99999999999)}"
        payer = f"user_{random.randint(100, 999)}@okaxis"
        app_name = random.choice(["PhonePe", "GooglePay", "Paytm", "BHIM"])
        
        # Inject intentional fraud on the last transaction if requested
        is_fraud = (req.inject_fraud and i == req.num_transactions - 1)
        
        if is_fraud:
            utr = "499999999999" # Flagged duplicate or invalid
            fraud_payload = {
                "utr": utr,
                "amount": amt,
                "merchant_vpa": m_data["profile"]["upi_id"],
                "timestamp_str": (datetime.now() + timedelta(hours=1)).isoformat(), # Future timestamp
                "payer_vpa": "scammer@fakeupi",
                "screenshot_metadata": {"font_mismatch_detected": True}
            }
            fraud_res = shield.verify_payment_claim(fraud_payload)
            status = "FRAUD_BLOCKED"
            voice_announced = False
        else:
            status = "SUCCESS"
            voice_announced = True
            total_added_volume += amt
            
        tx = {
            "tx_id": f"TXN_LIVE_{random.randint(100000, 999999)}",
            "utr": utr,
            "merchant_id": m_id,
            "amount": amt,
            "timestamp": datetime.now().isoformat(),
            "payer_vpa": payer,
            "payer_app": app_name,
            "status": status,
            "voice_soundbox_announced": voice_announced,
            "is_fraud_detected": is_fraud
        }
        
        generated_txs.append(tx)
        m_data["recent_transactions"].insert(0, tx)
        
    # Update monthly volume & re-evaluate SetuScore dynamically
    m_data["features"]["monthly_upi_volume"] += total_added_volume
    m_data["features"]["daily_tx_count"] += int(req.num_transactions / 5)
    
    uw = get_underwriter()
    new_eval = uw.evaluate_merchant(m_data["features"])
    m_data["underwriting"] = new_eval
    
    return {
        "simulated_count": req.num_transactions,
        "added_turnover": total_added_volume,
        "transactions": generated_txs,
        "new_setu_score": new_eval["setu_score"],
        "new_risk_tier": new_eval["risk_tier"],
        "updated_features": m_data["features"]
    }

@app.get("/api/analytics/research-macro")
def get_macro_research_analytics():
    """
    Returns verified macroeconomic and empirical datasets matching the research paper
    (RBI FI-Index trends, Gender gap metrics, Payment preference distributions, and PM SVANidhi disbursements).
    """
    return {
        "rbi_fi_index_progression": [
            {"year": "March 2021", "composite_index": 53.9, "access": 73.3, "usage": 43.0, "quality": 50.7},
            {"year": "March 2022", "composite_index": 56.4, "access": 73.8, "usage": 47.7, "quality": 51.5},
            {"year": "March 2023", "composite_index": 60.1, "access": 74.2, "usage": 53.8, "quality": 52.6},
            {"year": "March 2024", "composite_index": 64.2, "access": 74.8, "usage": 59.9, "quality": 54.0},
            {"year": "March 2025", "composite_index": 67.0, "access": 75.3, "usage": 64.2, "quality": 55.4},
            {"year": "March 2026", "composite_index": 70.0, "access": 75.9, "usage": 69.1, "quality": 56.8}
        ],
        "gender_digital_inclusion_gap": [
            {"demographic": "Urban Male", "inclusion_pct": 78, "color": "#3B82F6"},
            {"demographic": "Urban Female", "inclusion_pct": 57, "color": "#EC4899"},
            {"demographic": "Rural Male", "inclusion_pct": 61, "color": "#10B981"},
            {"demographic": "Rural Female", "inclusion_pct": 38, "color": "#F59E0B"}
        ],
        "payment_mode_market_share": [
            {"mode": "UPI (P2M & P2P)", "share_pct": 84.0, "avg_ticket": 140, "color": "#4F46E5"},
            {"mode": "Debit Cards", "share_pct": 8.5, "avg_ticket": 1250, "color": "#06B6D4"},
            {"mode": "Credit Cards", "share_pct": 4.5, "avg_ticket": 5200, "color": "#F43F5E"},
            {"mode": "NetBanking / IMPS", "share_pct": 3.0, "avg_ticket": 8900, "color": "#8B5CF6"}
        ],
        "pm_svanidhi_national_impact": {
            "total_disbursed_crore": 13797,
            "total_beneficiaries_lakh": 68.4,
            "total_digital_txs_crore": 557,
            "digital_tx_value_lakh_crore": 6.09,
            "tranche_1_disbursed_pct": 68.2,
            "tranche_2_disbursed_pct": 24.5,
            "tranche_3_disbursed_pct": 7.3,
            "repayment_rate_pct": 91.8
        },
        "informal_worker_income_differential": {
            "digital_integrated_avg_monthly_inr": 15800,
            "non_digital_peer_avg_monthly_inr": 11300,
            "income_premium_pct": 39.8,
            "source": "Mallick & Singla (2025) NSSO/PLFS synthesis"
        }
    }

# Serve static frontend files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "MicroSetu API is running. Frontend static directory initializing..."})

if __name__ == "__main__":
    import uvicorn
    print("Starting MicroSetu FinTech Server on http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
