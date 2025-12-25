from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime, timedelta
from shared.security import sign_token_data 

app = FastAPI(title="Offline Escrow - Token Management Service")

DENOMINATIONS = [1000, 500, 200, 100]
tokens_db = {} 

class Token(BaseModel):
    token_id: str
    issuer_wallet_id: str
    denomination: int
    expiry_time: str
    signature: str

class MintRequest(BaseModel):
    wallet_id: str
    amount: float

@app.post("/tokens/mint", response_model=List[Token])
async def mint_tokens(request: MintRequest):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    tokens = []
    remaining = request.amount
    for value in DENOMINATIONS:
        while remaining >= value:
            t_id = str(uuid.uuid4())
            expiry = (datetime.utcnow() + timedelta(days=2)).isoformat()
            payload_to_sign = f"{t_id}|{request.wallet_id}|{value}|{expiry}"
            
            token = Token(
                token_id=t_id,
                issuer_wallet_id=request.wallet_id,
                denomination=value,
                expiry_time=expiry,
                signature=sign_token_data(payload_to_sign)
            )
            tokens.append(token)
            # Store in memory
            tokens_db[t_id] = {"status": "ISSUED", "data": token}
            remaining -= value
    return tokens

# --- THE MISSING ENDPOINT ---
# escrow-backend/token-service/main.py

@app.get("/tokens/wallet/{wallet_id}")
async def list_wallet_tokens(wallet_id: str):
    """Returns tokens currently held in memory for this wallet."""
    # CHANGE: Use v["data"].issuer_wallet_id instead of v["data"]["issuer_wallet_id"]
    user_tokens = [
        v["data"] for k, v in tokens_db.items() 
        if v["data"].issuer_wallet_id == wallet_id 
    ]
    return user_tokens

@app.get("/tokens/metadata/{token_id}")
async def get_token_metadata(token_id: str):
    token = tokens_db.get(token_id)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return token