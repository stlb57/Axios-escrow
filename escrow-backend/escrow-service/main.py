from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
# --- Database Setup ---
DATABASE_URL = "sqlite:///./wallets.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(String, unique=True, index=True)
    spendable_balance = Column(Float, default=2450.0) # Initial mock balance
    escrow_locked = Column(Float, default=0.0)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BlueMint - Persistent Wallet Service")



# ... (after app = FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class EscrowRequest(BaseModel):
    wallet_id: str
    amount_to_lock: float

@app.post("/wallet/lock-escrow")
async def lock_escrow(request: EscrowRequest):
    db = SessionLocal()
    wallet = db.query(Wallet).filter(Wallet.wallet_id == request.wallet_id).first()
    
    # If wallet doesn't exist, create it for this demo
    if not wallet:
        wallet = Wallet(wallet_id=request.wallet_id)
        db.add(wallet)
        db.commit()

    if wallet.spendable_balance < request.amount_to_lock:
        db.close()
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Atomic Move in DB
    wallet.spendable_balance -= request.amount_to_lock
    wallet.escrow_locked += request.amount_to_lock
    
    db.commit()
    res = {"new_spendable": wallet.spendable_balance, "new_escrow": wallet.escrow_locked}
    db.close()
    return res

@app.get("/wallet/{wallet_id}/balance")
async def get_balance(wallet_id: str):
    db = SessionLocal()
    try:
        wallet = db.query(Wallet).filter(Wallet.wallet_id == wallet_id).first()
        if not wallet:
            return {"spendable_balance": 2450.0, "escrow_locked": 0.0}
        return wallet
    finally:
        db.close() # Always executes