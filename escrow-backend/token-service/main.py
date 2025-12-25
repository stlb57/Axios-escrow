from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime, timedelta
# Import the real signing logic
from shared.security import sign_token_data 

app = FastAPI(title="Offline Escrow - Token Management Service")

DENOMINATIONS = [1000, 500, 200, 100] # cite: 3081-3084
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

def create_token_bundle(wallet_id: str, total_amount: float) -> List[Token]:
    tokens = []
    remaining = total_amount
    
    for value in DENOMINATIONS:
        while remaining >= value:
            t_id = str(uuid.uuid4())
            expiry = (datetime.utcnow() + timedelta(days=2)).isoformat()
            
            # The exact string format used for the signature (cite: 3055)
            # Reconstructing this incorrectly will cause verification to fail.
            payload_to_sign = f"{t_id}|{wallet_id}|{value}|{expiry}"
            
            token = Token(
                token_id=t_id,
                issuer_wallet_id=wallet_id,
                denomination=value,
                expiry_time=expiry,
                signature=sign_token_data(payload_to_sign) # Real Ed25519 signature
            )
            tokens.append(token)
            # Store metadata for server-side verification later
            tokens_db[t_id] = {"status": "ISSUED", "data": token}
            remaining -= value
            
    return tokens

@app.post("/tokens/mint", response_model=List[Token])
async def mint_tokens(request: MintRequest):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    return create_token_bundle(request.wallet_id, request.amount)

@app.get("/tokens/metadata/{token_id}")
async def get_token_metadata(token_id: str):
    token = tokens_db.get(token_id)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return token