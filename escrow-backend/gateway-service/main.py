import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(title="BlueMint - API Gateway & App Host")

# --- 1. ENABLE CORS (Essential for Browser Testing) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your browser to talk to the backend
    allow_methods=["*"],
    allow_headers=["*"],
)

# Internal Service URLs
AUTH_URL = "http://localhost:8000"
ESCROW_URL = "http://localhost:8001"
TOKEN_URL = "http://localhost:8002"

class OfflineStartRequest(BaseModel):
    wallet_id: str
    phone: str
    amount: float
    integrity_report: dict

# --- 2. SERVE THE FRONTEND FILES ---
# This links the 'escrow-wallet' folder to the /app URL
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.abspath(os.path.join(current_dir, "../../escrow-wallet"))
app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="app")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# --- 3. EXISTING API LOGIC ---
@app.post("/gateway/prepare-offline")
async def prepare_offline_session(request: OfflineStartRequest):
    async with httpx.AsyncClient() as client:
        # 1. Verify Integrity (cite: 1319)
        auth_resp = await client.post(f"{AUTH_URL}/auth/verify-integrity", json=request.integrity_report)
        if auth_resp.json().get("status") != "secure":
            raise HTTPException(status_code=403, detail="Device integrity compromised.")

        # 2. Lock Escrow Funds (cite: 530)
        escrow_resp = await client.post(f"{ESCROW_URL}/wallet/lock-escrow", json={
            "wallet_id": request.wallet_id,
            "amount_to_lock": request.amount
        })
        
        # 3. Mint Tokens (cite: 743)
        token_resp = await client.post(f"{TOKEN_URL}/tokens/mint", json={
            "wallet_id": request.wallet_id,
            "amount": request.amount
        })
        
        return {
            "status": "ready",
            "tokens": token_resp.json(),
            "message": "Offline session initialized."
        }