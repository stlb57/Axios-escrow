from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from shared.security import verify_token_signature

# --- Database Setup ---
DATABASE_URL = "sqlite:///./ledger.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class LedgerEntry(Base):
    __tablename__ = "ledger"
    id = Column(String, primary_key=True) # entry_id
    payment_request_id = Column(String, unique=True)
    merchant_id = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SpentToken(Base):
    __tablename__ = "spent_tokens"
    token_id = Column(String, primary_key=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BlueMint - Persistent Ledger Service")

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
    
    # 1. Idempotency Check
    exists = db.query(LedgerEntry).filter(LedgerEntry.payment_request_id == request.payment_request_id).first()
    if exists:
        db.close()
        return {"status": "already_settled"}

    total_amount = 0
    valid_ids = []

    # 2. Token Verification
    for token in request.tokens:
        # Check if already spent in DB
        is_spent = db.query(SpentToken).filter(SpentToken.token_id == token.token_id).first()
        if is_spent:
            db.close()
            raise HTTPException(status_code=400, detail=f"Token {token.token_id} already used")

        # Crypto Verify
        data = f"{token.token_id}|{token.issuer_wallet_id}|{token.denomination}|{token.expiry_time}"
        if not verify_token_signature(data, token.signature):
            db.close()
            raise HTTPException(status_code=401, detail="Invalid signature")

        total_amount += token.denomination
        valid_ids.append(token.token_id)

    # 3. Save to Ledger & Mark Spent
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
    return {"status": "success", "amount_settled": total_amount}