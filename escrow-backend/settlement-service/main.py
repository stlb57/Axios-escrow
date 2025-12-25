from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime
# Import the real verification logic
from shared.security import verify_token_signature 

app = FastAPI(title="Offline Escrow - Settlement & Ledger Service")

ledger_db = [] 
spent_tokens = set() # Enforces single-use invariant (cite: 3178, 4425)

# Mock merchant database
merchants_db = {
    "MCH-CAFE-X": {"name": "CafeX Store", "balance": 0.0}
}

class TokenPayload(BaseModel):
    token_id: str
    issuer_wallet_id: str
    denomination: int
    expiry_time: str
    signature: str

class SettlementRequest(BaseModel):
    merchant_id: str
    payment_request_id: str 
    tokens: List[TokenPayload] # Merchant sends the full token objects

@app.post("/settle")
async def settle_payment(request: SettlementRequest):
    # 1. Idempotency Check (cite: 3494, 4462)
    for entry in ledger_db:
        if entry["payment_request_id"] == request.payment_request_id:
            return {"status": "already_settled", "detail": "Transaction already processed."}

    merchant = merchants_db.get(request.merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    total_to_credit = 0.0
    valid_token_ids = []

    # 2. Strict Cryptographic & Business Verification
    for token in request.tokens:
        # Check single-use invariant (cite: 3458, 4425)
        if token.token_id in spent_tokens:
            raise HTTPException(status_code=400, detail=f"Token {token.token_id} already spent")
        
        # Reconstruct the payload exactly as it was signed
        data_to_verify = f"{token.token_id}|{token.issuer_wallet_id}|{token.denomination}|{token.expiry_time}"
        
        # Verify the Ed25519 signature (cite: 3479, 3592)
        if not verify_token_signature(data_to_verify, token.signature):
            raise HTTPException(status_code=401, detail=f"Invalid cryptographic signature for token {token.token_id}")

        # Check for expiry using server time (cite: 3457, 4441)
        if datetime.fromisoformat(token.expiry_time) < datetime.utcnow():
            raise HTTPException(status_code=400, detail=f"Token {token.token_id} has expired")

        valid_token_ids.append(token.token_id)
        total_to_credit += token.denomination

    # 3. Atomic Transaction (cite: 3452, 4449)
    try:
        for t_id in valid_token_ids:
            spent_tokens.add(t_id)
        
        merchant["balance"] += total_to_credit
        
        ledger_entry = {
            "entry_id": str(uuid.uuid4()),
            "payment_request_id": request.payment_request_id,
            "merchant_id": request.merchant_id,
            "amount": total_to_credit,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "SETTLED"
        }
        ledger_db.append(ledger_entry) # Immutable ledger fact (cite: 3507, 4469)
        
        return {
            "status": "success",
            "settled_amount": total_to_credit,
            "merchant_balance": merchant["balance"]
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Database atomicity failure during settlement")