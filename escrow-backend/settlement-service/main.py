from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from shared.security import verify_token_signature
from sqlalchemy import func
import httpx # Required for service-to-service communication

# --- Database Setup ---
DATABASE_URL = "sqlite:///./ledger.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class LedgerEntry(Base):
    __tablename__ = "ledger"
    id = Column(String, primary_key=True)
    payment_request_id = Column(String, unique=True)
    merchant_id = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SpentToken(Base):
    __tablename__ = "spent_tokens"
    token_id = Column(String, primary_key=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BlueMint - Persistent Ledger Service")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenPayload(BaseModel):
    token_id: str
    issuer_wallet_id: str
    denomination: int
    expiry_time: str
    signature: str

class SettlementRequest(BaseModel):
    merchant_id: str
    payment_request_id: str
    tokens: List[TokenPayload]

@app.post("/settle")
async def settle_payment(request: SettlementRequest):
    db = SessionLocal()
    
    # 1. Idempotency Check (cite: 8)
    exists = db.query(LedgerEntry).filter(LedgerEntry.payment_request_id == request.payment_request_id).first()
    if exists:
        db.close()
        return {"status": "already_settled"}

    total_amount = 0
    valid_ids = []
    issuer_id = request.tokens[0].issuer_wallet_id if request.tokens else None

    # 2. Token Verification (cite: 8, 9)
    for token in request.tokens:
        is_spent = db.query(SpentToken).filter(SpentToken.token_id == token.token_id).first()
        if is_spent:
            db.close()
            raise HTTPException(status_code=400, detail=f"Token {token.token_id} already used")

        data = f"{token.token_id}|{token.issuer_wallet_id}|{token.denomination}|{token.expiry_time}"
        if not verify_token_signature(data, token.signature):
            db.close()
            raise HTTPException(status_code=401, detail="Invalid signature")

        total_amount += token.denomination
        valid_ids.append(token.token_id)

    # 3. Save to Ledger & Mark Spent (cite: 8)
    new_entry = LedgerEntry(
        id=str(uuid.uuid4()),
        payment_request_id=request.payment_request_id,
        merchant_id=request.merchant_id,
        amount=total_amount
    )
    db.add(new_entry)
    for t_id in valid_ids:
        db.add(SpentToken(token_id=t_id))

    db.commit()
    db.close()

    # --- 4. RECONCILIATION: Burn the USER'S LOCKED BALANCE ---
    if issuer_id and total_amount > 0:
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8001/wallet/burn-escrow", json={
                "wallet_id": issuer_id,
                "amount": total_amount
            })

    return {"status": "success", "amount_settled": total_amount}

@app.get("/merchant/{merchant_id}/earnings")
async def get_merchant_earnings(merchant_id: str):
    db = SessionLocal()
    try:
        total = db.query(func.sum(LedgerEntry.amount)).filter(LedgerEntry.merchant_id == merchant_id).scalar()
        return {"merchant_id": merchant_id, "total_earnings": total or 0.0}
    finally:
        db.close()