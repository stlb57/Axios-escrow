from fastapi import FastAPI, HTTPException

app = FastAPI(title="Offline Escrow - Dispute & Admin Service")

# Mock connection to Settlement Ledger (Port 8003)
@app.get("/admin/audit/{request_id}")
async def audit_transaction(request_id: str):
    """
    Forensic analysis: Reconstructs who paid whom and when.
    Used for Dispute Resolution (cite: 6.17, 7.15).
    """
    # In production, this queries the Settlement Service for ledger data
    return {
        "payment_request_id": request_id,
        "verified_settlement": True,
        "audit_trail": [
            {"event": "ESCROW_LOCKED", "timestamp": "2025-12-25T14:00:00"},
            {"event": "TOKEN_MINTED", "token_id": "T-99", "timestamp": "2025-12-25T14:05:00"},
            {"event": "SETTLED_BY_MERCHANT", "merchant_id": "MCH-CAFE-X", "timestamp": "2025-12-25T21:00:00"}
        ]
    }