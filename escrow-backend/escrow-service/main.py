from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="Offline Escrow - Wallet & Escrow Service")

# --- Mock Database ---
# Linking to the Wallet IDs from your frontend (profile.html)
wallets_db = {
    "WLT-8F3A-92KD": {
        "owner": "Rajesh Kumar",
        "spendable_balance": 2450.00, # Matching index.html
        "escrow_locked": 0.00,
        "currency": "INR"
    }
}

# --- Schemas ---
class EscrowRequest(BaseModel):
    wallet_id: str
    amount_to_lock: float

# --- Business Logic: Escrow Invariants ---
# cite: 539, 638, 2049
def validate_escrow_move(wallet_id: str, amount: float):
    wallet = wallets_db.get(wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    # Invariant: Escrow must be backed by real balance (cite: 2039)
    if wallet["spendable_balance"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance to lock escrow")
    
    # Invariant: Escrow cap (cite: 539, 622)
    if (wallet["escrow_locked"] + amount) > 5000.00:
        raise HTTPException(status_code=400, detail="Escrow limit reached (Max ₹5,000)")
    
    return wallet

# --- API Endpoints ---

@app.get("/wallet/{wallet_id}/balance")
async def get_balance(wallet_id: str):
    """Used by index.html to show balance card info."""
    wallet = wallets_db.get(wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

@app.post("/wallet/lock-escrow")
async def lock_escrow(request: EscrowRequest):
    """
    Moves money from spendable to locked escrow.
    This is Phase 1 of the Escrow Lifecycle (cite: 524, 530).
    """
    wallet = validate_escrow_move(request.wallet_id, request.amount_to_lock)
    
    # Atomic Move: This must be one transaction in a real DB (cite: 1095, 2091)
    wallet["spendable_balance"] -= request.amount_to_lock
    wallet["escrow_locked"] += request.amount_to_lock
    
    return {
        "status": "success",
        "wallet_id": request.wallet_id,
        "new_spendable": wallet["spendable_balance"],
        "new_escrow": wallet["escrow_locked"],
        "message": f"₹{request.amount_to_lock} is now locked for offline use."
    }