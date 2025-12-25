from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uuid
from datetime import datetime

app = FastAPI(title="Offline Escrow - Settlement & Ledger Service")

# --- Mock Databases ---
# In production, these are permanent tables in PostgreSQL (cite: 1146, 1150)
ledger_db = [] 
spent_tokens = set() # To enforce single-use invariant (cite: 842, 1101)

# Mock merchant database (cite: 1104)
merchants_db = {
    "MCH-CAFE-X": {"name": "CafeX Store", "balance": 0.0}
}

class SettlementRequest(BaseModel):
    merchant_id: str
    payment_request_id: str # For idempotency (cite: 1140)
    token_ids: List[str]

# --- Business Logic: The Atomic Settlement ---

@app.post("/settle")
async def settle_payment(request: SettlementRequest):
    """
    The only operation that moves money.
    Must be atomic and idempotent (cite: 1047, 1094, 1136).
    """
    # 1. Idempotency Check (cite: 1137, 1141)
    # Check if this exact payment request was already settled
    for entry in ledger_db:
        if entry["payment_request_id"] == request.payment_request_id:
            return {"status": "already_settled", "detail": "This payment was previously processed."}

    merchant = merchants_db.get(request.merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    total_to_credit = 0.0
    valid_tokens = []

    # 2. Token Verification (cite: 1119, 1120)
    for t_id in request.token_ids:
        # Invariant: Token single-use (cite: 1101, 2067)
        if t_id in spent_tokens:
            raise HTTPException(status_code=400, detail=f"Token {t_id} already spent")
        
        # In a real app, you would call the Token Service (Port 8002) 
        # to verify the cryptographic signature here (cite: 1122).
        # We'll simulate finding a ₹450 value for this demo.
        token_value = 450.0 
        valid_tokens.append(t_id)
        total_to_credit += token_value

    # 3. The Atomic Transaction (cite: 1095, 1106)
    # In production, this block is wrapped in a DB transaction
    try:
        # Mark tokens as spent
        for t_id in valid_tokens:
            spent_tokens.add(t_id)
        
        # Credit merchant (cite: 1104, 1169)
        merchant["balance"] += total_to_credit
        
        # Write Immutable Ledger Entry (cite: 1105, 1146, 1157)
        ledger_entry = {
            "entry_id": str(uuid.uuid4()),
            "payment_request_id": request.payment_request_id,
            "merchant_id": request.merchant_id,
            "amount": total_to_credit,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "SETTLED"
        }
        ledger_db.append(ledger_entry)
        
        return {
            "status": "success",
            "settled_amount": total_to_credit,
            "merchant_balance": merchant["balance"],
            "ledger_id": ledger_entry["entry_id"]
        }
    except Exception as e:
        # If any step failed, rollback logic would go here (cite: 1106)
        raise HTTPException(status_code=500, detail="Settlement failed during processing")

@app.get("/ledger")
async def view_ledger():
    """Provides data for the 'History' screen (cite: history.html)."""
    return ledger_db