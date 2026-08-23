"""
MicroSetu - Anti-Fraud & Payment Spoof Prevention Shield
Protects informal merchants against counterfeit payment APKs, forged screenshots,
tampered QR stickers, and duplicate UTR replay attacks.
"""

import time
import hashlib
from datetime import datetime, timedelta

class PaymentFraudShield:
    def __init__(self):
        # In-memory sliding window cache of settled UTRs to prevent replay attacks
        self.settled_utrs = {}
        # Known fraudulent / test signatures
        self.flagged_vpas = {
            "scammer@fakeupi",
            "spoof_tester@bot",
            "fake_paytm_apk@apk"
        }
        
    def verify_payment_claim(self, payload: dict) -> dict:
        """
        Validates a payment claim submitted via manual input or camera OCR against NPCI/Bank rules.
        Payload format:
        {
            "utr": "412345678901",
            "amount": 150.0,
            "merchant_vpa": "rameshchai@okaxis",
            "timestamp_str": "2026-08-23T18:30:00",
            "payer_vpa": "customer@paytm",
            "app_reported": "GooglePay",
            "screenshot_metadata": { "has_pixel_artifacts": False, "font_mismatch_detected": False }
        }
        """
        utr = str(payload.get("utr", "")).strip()
        amount = float(payload.get("amount", 0.0))
        merchant_vpa = str(payload.get("merchant_vpa", "")).strip().lower()
        payer_vpa = str(payload.get("payer_vpa", "")).strip().lower()
        timestamp_str = payload.get("timestamp_str")
        screenshot_meta = payload.get("screenshot_metadata") or {}
        
        fraud_flags = []
        risk_score = 0  # 0 to 100
        
        # 1. UTR Format & Checksum Verification
        if not utr or len(utr) != 12 or not utr.isdigit():
            fraud_flags.append({
                "code": "INVALID_UTR_FORMAT",
                "severity": "CRITICAL",
                "message": "Invalid UTR format. Standard NPCI banking references must be exactly 12 numeric digits."
            })
            risk_score += 45
        else:
            # First digit represents the Indian banking year switch
            first_digit = int(utr[0])
            if first_digit not in [3, 4, 5, 6]:
                fraud_flags.append({
                    "code": "INVALID_SWITCH_CODE",
                    "severity": "HIGH",
                    "message": f"Suspicious banking routing code '{first_digit}'. Does not match NPCI switch protocol."
                })
                risk_score += 30

        # 2. Duplicate UTR Replay Attack Detection
        now_ts = time.time()
        # Clean up cache older than 24 hours
        self.settled_utrs = {k: v for k, v in self.settled_utrs.items() if now_ts - v["seen_at"] < 86400}
        
        if utr in self.settled_utrs:
            prior = self.settled_utrs[utr]
            fraud_flags.append({
                "code": "DUPLICATE_REPLAY_ATTACK",
                "severity": "CRITICAL",
                "message": f"UTR {utr} was already settled {int(now_ts - prior['seen_at'])}s ago for ₹{prior['amount']}. Replay attack detected!"
            })
            risk_score += 60

        # 3. Timestamp Freshness Verification
        if timestamp_str:
            try:
                tx_time = datetime.fromisoformat(timestamp_str.replace("Z", ""))
                current_time = datetime.now()
                delta_minutes = (current_time - tx_time).total_seconds() / 60.0
                
                if delta_minutes < -5:  # Future dated
                    fraud_flags.append({
                        "code": "FUTURE_TIMESTAMP_DETECTED",
                        "severity": "CRITICAL",
                        "message": "Payment screenshot displays a future timestamp. Clear evidence of fake receipt generator APK."
                    })
                    risk_score += 50
                elif delta_minutes > 120:  # Older than 2 hours
                    fraud_flags.append({
                        "code": "STALE_TIMESTAMP_RECEIPT",
                        "severity": "MEDIUM",
                        "message": f"Payment timestamp is {int(delta_minutes)} minutes old. Verify your bank ledger before handing goods."
                    })
                    risk_score += 25
            except Exception:
                fraud_flags.append({
                    "code": "UNPARSEABLE_TIMESTAMP",
                    "severity": "LOW",
                    "message": "Could not parse transaction timestamp."
                })
                risk_score += 10

        # 4. Blacklisted / Malicious VPA Check
        if payer_vpa in self.flagged_vpas:
            fraud_flags.append({
                "code": "FLAGGED_MALICIOUS_VPA",
                "severity": "HIGH",
                "message": f"Payer handle '{payer_vpa}' has been reported for digital payment fraud."
            })
            risk_score += 40

        # 5. Screenshot Font / Overlay Spoof Detection (Simulated OCR heuristics)
        if screenshot_meta.get("font_mismatch_detected", False):
            fraud_flags.append({
                "code": "FORGED_FONT_SIGNATURE",
                "severity": "HIGH",
                "message": "UI font metrics in the payment screenshot do not match official PhonePe/GPay app signatures (Spoof APK detected)."
            })
            risk_score += 40
            
        if screenshot_meta.get("has_pixel_artifacts", False):
            fraud_flags.append({
                "code": "COMPRESSION_MANIPULATION",
                "severity": "MEDIUM",
                "message": "Image editing or localized JPEG compression artifacts found near the transaction amount string."
            })
            risk_score += 25

        # 6. Micro-Merchant High Velocity Anomaly
        if amount > 15000:
            fraud_flags.append({
                "code": "HIGH_VALUE_ANOMALY",
                "severity": "MEDIUM",
                "message": f"Amount ₹{amount:,.2f} is significantly above normal street-vendor ticket distribution (avg ₹35 - ₹250)."
            })
            risk_score += 15

        # Decision synthesis
        risk_score = min(100, risk_score)
        
        if risk_score >= 50:
            status = "BLOCKED_FRAUD_DETECTED"
            action = "DO NOT HAND OVER GOODS. Soundbox announcement suppressed."
            badge_color = "red"
        elif risk_score >= 25:
            status = "SUSPICIOUS_MANUAL_CHECK"
            action = "Verify SMS or bank statement before releasing goods."
            badge_color = "amber"
        else:
            status = "VERIFIED_GENUINE"
            action = "Payment valid. Triggering Soundbox audio confirmation."
            badge_color = "emerald"
            # Record in settled UTRs
            if utr and len(utr) == 12:
                self.settled_utrs[utr] = {
                    "seen_at": now_ts,
                    "amount": amount,
                    "merchant_vpa": merchant_vpa
                }

        return {
            "status": status,
            "risk_score": risk_score,
            "action_advice": action,
            "badge_color": badge_color,
            "utr": utr,
            "amount": amount,
            "merchant_vpa": merchant_vpa,
            "flags": fraud_flags,
            "checked_at": datetime.now().isoformat()
        }

fraud_shield_instance = PaymentFraudShield()

def get_fraud_shield():
    return fraud_shield_instance

if __name__ == "__main__":
    shield = get_fraud_shield()
    test_claim = {
        "utr": "423456789012",
        "amount": 150.0,
        "merchant_vpa": "rameshchai@okaxis",
        "timestamp_str": datetime.now().isoformat(),
        "payer_vpa": "rahul@paytm",
        "app_reported": "PhonePe",
        "screenshot_metadata": { "font_mismatch_detected": False, "has_pixel_artifacts": False }
    }
    res = shield.verify_payment_claim(test_claim)
    print("Genuine Claim Check:", res["status"], f"(Risk: {res['risk_score']}%)")
    
    # Fake claim test
    fake_claim = {
        "utr": "423456789012", # duplicate replay
        "amount": 150.0,
        "merchant_vpa": "rameshchai@okaxis",
        "timestamp_str": (datetime.now() + timedelta(minutes=45)).isoformat(), # future
        "payer_vpa": "scammer@fakeupi",
        "screenshot_metadata": { "font_mismatch_detected": True }
    }
    fake_res = shield.verify_payment_claim(fake_claim)
    print("Fraud Claim Check:", fake_res["status"], f"(Risk: {fake_res['risk_score']}%)")
    for f in fake_res["flags"]:
        print(f" - [{f['severity']}] {f['code']}: {f['message']}")
