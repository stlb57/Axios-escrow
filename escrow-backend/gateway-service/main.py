import httpx # You'll need to run 'pip install httpx'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Offline Escrow - API Gateway")

# Internal Service URLs (In DevOps, these would be in a config file or env vars)
AUTH_URL = "http://localhost:8000"
ESCROW_URL = "http://localhost:8001"
TOKEN_URL = "http://localhost:8002"

class OfflineStartRequest(BaseModel):
    wallet_id: str
    phone: str
    amount: float
    integrity_report: dict

@app.post("/gateway/prepare-offline")
async def prepare_offline_session(request: OfflineStartRequest):
    """
    Orchestrates the sequence: Integrity Check -> Lock Escrow -> Mint Tokens.
    This simplifies the logic for the Android app (cite: index.html).
    """
    async with httpx.AsyncClient() as client:
        # 1. Verify Integrity (cite: 7.8, 1319)
        auth_resp = await client.post(f"{AUTH_URL}/auth/verify-integrity", json=request.integrity_report)
        if auth_resp.json().get("status") != "secure":
            raise HTTPException(status_code=403, detail="Device integrity compromised. Session denied.")

        # 2. Lock Escrow Funds (cite: 3.5, 530)
        escrow_resp = await client.post(f"{ESCROW_URL}/wallet/lock-escrow", json={
            "wallet_id": request.wallet_id,
            "amount_to_lock": request.amount
        })
        if escrow_resp.status_code != 200:
            raise HTTPException(status_code=escrow_resp.status_code, detail="Failed to lock escrow.")

        # 3. Mint Tokens (cite: 4.8, 743)
        token_resp = await client.post(f"{TOKEN_URL}/tokens/mint", json={
            "wallet_id": request.wallet_id,
            "amount": request.amount
        })
        
        return {
            "status": "ready",
            "tokens": token_resp.json(),
            "message": "Offline session initialized. Tokens ready for Bluetooth transfer."
        }