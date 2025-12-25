from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import jwt # PyJWT
from datetime import datetime, timedelta

app = FastAPI(title="Offline Escrow - Identity & Auth Service")

# --- Mock Database (Use PostgreSQL in Production) ---
users_db = {
    "919876543210": {
        "name": "Rajesh Kumar",
        "wallet_id": "WLT-8F3A-92KD",
        "phone": "+919876543210",
        "is_verified": True,
        "is_merchant": False
    }
}

# --- Configuration ---
SECRET_KEY = "server_private_key_do_not_leak" # cite: 1279
ALGORITHM = "HS256"

# --- Schemas ---
class IntegrityReport(BaseModel):
    device_id: str
    is_rooted: bool # cite: 1313
    app_signature_valid: bool # cite: 1310
    has_debugger: bool # cite: 1316
    is_emulator: bool # cite: 1318

class LoginRequest(BaseModel):
    phone: str
    password: str

# --- Business Logic: Integrity Check ---
def verify_device_health(report: IntegrityReport):
    """
    Implements the 'Integrity-gated offline mode' invariant.
    Fails closed if any check fails. [cite: 1319, 2124]
    """
    if report.is_rooted or not report.app_signature_valid or report.has_debugger or report.is_emulator:
        return False
    return True

# --- API Endpoints ---

@app.post("/auth/login")
async def login(request: LoginRequest):
    user = users_db.get(request.phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # In a real app, verify password hash here
    token_data = {"sub": user["phone"], "wallet_id": user["wallet_id"], "exp": datetime.utcnow() + timedelta(days=1)}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": token, "token_type": "bearer", "user": user}

@app.post("/auth/verify-integrity")
async def verify_integrity(report: IntegrityReport):
    """
    Endpoint for the 'Refresh' button on the profile.html page.
    Determines if the device can proceed to use offline tokens. [cite: 1320]
    """
    is_healthy = verify_device_health(report)
    
    if not is_healthy:
        return {
            "status": "compromised",
            "offline_mode_enabled": False,
            "message": "Security integrity check failed. Offline mode disabled." # cite: 1409
        }
    
    return {
        "status": "secure",
        "offline_mode_enabled": True,
        "message": "Device verified and secure." # cite: profile.html
    }

@app.get("/auth/profile/{wallet_id}")
async def get_profile(wallet_id: str):
    # Fetch user data for index.html / profile.html
    for phone, user in users_db.items():
        if user["wallet_id"] == wallet_id:
            return user
    raise HTTPException(status_code=404, detail="Profile not found")