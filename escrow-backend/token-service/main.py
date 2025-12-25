from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
import secrets
from datetime import datetime, timedelta

app = FastAPI(title="Offline Escrow - Token Management Service")

# --- Configuration ---
# cite: 724, 726, 727
DENOMINATIONS = [1000, 500, 200, 100] 

# --- Mock Database ---
# Tracks which tokens have been minted (cite: 767, 772)
tokens_db = {} 

class Token(BaseModel):
    token_id: str
    issuer_wallet_id: str
    denomination: int
    expiry_time: str
    signature: str

class MintRequest(BaseModel):
    wallet_id: str
    amount: float # This must match what was locked in Escrow Service

# --- Business Logic ---

def generate_signature(payload: str):
    """Simulates a cryptographic server signature (cite: 709, 1279)."""
    return f"SIG_{secrets.token_hex(16)}"

def create_token_bundle(wallet_id: str, total_amount: float) -> List[Token]:
    """Breakdown total escrow into fixed denomination tokens (cite: 745)."""
    tokens = []
    remaining = total_amount
    
    # Simple algorithm to minimize token count (cite: 761, 764)
    for value in DENOMINATIONS:
        while remaining >= value:
            t_id = str(uuid.uuid4())
            expiry = (datetime.utcnow() + timedelta(days=2)).isoformat()
            
            payload = f"{t_id}|{wallet_id}|{value}|{expiry}"
            token = Token(
                token_id=t_id,
                issuer_wallet_id=wallet_id,
                denomination=value,
                expiry_time=expiry,
                signature=generate_signature(payload)
            )
            tokens.append(token)
            tokens_db[t_id] = {"status": "ISSUED", "data": token}
            remaining -= value
            
    return tokens

# --- API Endpoints ---

@app.post("/tokens/mint", response_model=List[Token])
async def mint_tokens(request: MintRequest):
    """
    Converts escrowed value into portable tokens.
    Requirement: User must be online and integrity-verified (cite: 739, 740).
    """
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # In a full system, this service would call the Escrow Service 
    # to verify the wallet actually has this much locked (cite: 742).
    
    new_tokens = create_token_bundle(request.wallet_id, request.amount)
    return new_tokens

@app.get("/tokens/validate/{token_id}")
async def validate_token(token_id: str):
    """Used later by the Settlement service to check a token's health."""
    token = tokens_db.get(token_id)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return token