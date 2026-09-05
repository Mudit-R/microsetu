"""
Automated Integration and Unit Tests for MicroSetu Platform
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root and backend to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from backend.server import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "model_metadata" in data
    assert data["model_metadata"]["auc_roc"] > 0.90

def test_list_merchants():
    response = client.get("/api/merchants")
    assert response.status_code == 200
    data = response.json()
    assert len(data["merchants"]) >= 5
    first_m = data["merchants"][0]
    assert "setu_score" in first_m
    assert first_m["setu_score"] >= 300

def test_get_merchant_details():
    response = client.get("/api/merchants/MERCH_RAMESH_001")
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["name"] == "Ramesh Kumar (Ramesh Tea Stall)"
    assert "underwriting" in data
    assert "ledger" in data
    assert "cashflow_forecast" in data
    assert len(data["recent_transactions"]) > 0

def test_ml_underwriting():
    payload = {
        "merchant_id": "MERCH_RAMESH_001",
        "tenure_months": 28,
        "active_days_per_month": 29,
        "daily_tx_count": 110,
        "avg_ticket_size": 35,
        "ticket_size_variance": 12,
        "monthly_upi_volume": 111650,
        "repeat_customer_ratio": 0.58,
        "cashflow_volatility_cv": 0.18,
        "uses_audio_soundbox": 1,
        "failed_dispute_rate": 0.4,
        "prior_svanidhi_tier": 2,
        "on_time_repayment_ratio": 0.98
    }
    response = client.post("/api/underwrite", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["setu_score"] >= 700
    assert data["approved_credit_limit"] == 50000
    assert len(data["top_positive_drivers"]) > 0

def test_fraud_detector_genuine():
    from datetime import datetime
    payload = {
        "utr": "412345678901",
        "amount": 50.0,
        "merchant_vpa": "rameshchai@okaxis",
        "timestamp_str": datetime.now().isoformat(),
        "payer_vpa": "valid_user@okaxis",
        "app_reported": "PhonePe"
    }
    response = client.post("/api/fraud-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VERIFIED_GENUINE"
    assert data["risk_score"] < 25

def test_fraud_detector_spoof_detection():
    from datetime import datetime, timedelta
    payload = {
        "utr": "999999", # Invalid format
        "amount": 25000.0, # High anomaly
        "merchant_vpa": "rameshchai@okaxis",
        "timestamp_str": (datetime.now() + timedelta(hours=5)).isoformat(), # Future timestamp
        "payer_vpa": "scammer@fakeupi",
        "screenshot_metadata": { "font_mismatch_detected": True }
    }
    response = client.post("/api/fraud-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "BLOCKED_FRAUD_DETECTED"
    assert data["risk_score"] >= 50
    assert len(data["flags"]) >= 2

def test_vernacular_voice_ledger_parser():
    payload = {
        "merchant_id": "MERCH_RAMESH_001",
        "text_transcript": "Aaj 450 rupaye ki sabzi kharidi mandi se"
    }
    response = client.post("/api/voice-ledger/parse", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["parsed_data"]["entry_type"] == "EXPENSE"
    assert data["parsed_data"]["amount"] == 450.0
    assert "Produce" in data["parsed_data"]["category"] or "Vegetables" in data["parsed_data"]["category"]

def test_cashflow_forecast():
    response = client.get("/api/cashflow/forecast?base_daily_revenue=3000&horizon_days=30")
    assert response.status_code == 200
    data = response.json()
    assert len(data["forecast_data"]) == 30
    assert data["summary"]["projected_30d_turnover"] > 50000

def test_live_burst_simulation():
    payload = {
        "merchant_id": "MERCH_RAMESH_001",
        "num_transactions": 5,
        "inject_fraud": False
    }
    response = client.post("/api/simulate/burst", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["simulated_count"] == 5
    assert len(data["transactions"]) == 5

def test_macro_research_analytics():
    response = client.get("/api/analytics/research-macro")
    assert response.status_code == 200
    data = response.json()
    assert len(data["rbi_fi_index_progression"]) >= 6
    assert data["pm_svanidhi_national_impact"]["total_disbursed_crore"] == 13797

def test_static_index_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "MicroSetu" in response.text
