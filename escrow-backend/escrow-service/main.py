from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware

# --- Database Setup (cite: 5) ---
DATABASE_URL = "sqlite:///./wallets.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(String, unique=True, index=True)
    spendable_balance = Column(Float, default=2450.0)
    escrow_locked = Column(Float, default=0.0)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BlueMint - Persistent Wallet Service")

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
    """Moves money from Spendable to Locked (Pre-locking for Offline)."""
    db = SessionLocal()
    wallet = db.query(Wallet).filter(Wallet.wallet_id == request.wallet_id).first()
    
    if not wallet:
        wallet = Wallet(wallet_id=request.wallet_id)
        db.add(wallet)
        db.commit()

    if wallet.spendable_balance < request.amount_to_lock:
        db.close()
        raise HTTPException(status_code=400, detail="Insufficient balance")

    wallet.spendable_balance -= request.amount_to_lock
    wallet.escrow_locked += request.amount_to_lock
    
    db.commit()
    res = {"new_spendable": wallet.spendable_balance, "new_escrow": wallet.escrow_locked}
    db.close()
    return res

# --- NEW: BURN ESCROW ENDPOINT ---
@app.post("/wallet/burn-escrow")
async def burn_escrow(request: dict):
    """Permanently removes funds from the Locked Vault once settled."""
    db = SessionLocal()
    wallet_id = request.get('wallet_id')
    amount = request.get('amount')
    
    print(f"🔥 SETTLEMENT RECEIVED: Burning ₹{amount} from {wallet_id}'s locked vault.")
    
    wallet = db.query(Wallet).filter(Wallet.wallet_id == wallet_id).first()
    if wallet:
        wallet.escrow_locked -= amount
        db.commit()
        print(f"✅ Success. New Locked Balance: ₹{wallet.escrow_locked}")
    db.close()
    return {"status": "burned"}

# --- NEW: ADMIN TOPUP ENDPOINT ---
@app.post("/wallet/admin/topup")
async def admin_topup(wallet_id: str, amount: float):
    """Admin tool to add funds (e.g., adding your ₹50k)."""
    db = SessionLocal()
    wallet = db.query(Wallet).filter(Wallet.wallet_id == wallet_id).first()
    if not wallet:
        wallet = Wallet(wallet_id=wallet_id, spendable_balance=amount)
        db.add(wallet)
    else:
        wallet.spendable_balance += amount
    db.commit()
    db.close()
    return {"message": f"Added ₹{amount}", "new_balance": wallet.spendable_balance}

@app.get("/wallet/{wallet_id}/balance")
async def get_balance(wallet_id: str):
    db = SessionLocal()
    try:
        wallet = db.query(Wallet).filter(Wallet.wallet_id == wallet_id).first()
        if not wallet:
            return {"spendable_balance": 2450.0, "escrow_locked": 0.0}
        return wallet
    finally:
        db.close()
# @app.post("/wallet/release-escrow")
# async def release_escrow(request: EscrowRequest):
#     """Reverses the lock: moves money from Escrow back to Spendable Balance."""
#     db = SessionLocal()
#     try:
#         wallet = db.query(Wallet).filter(Wallet.wallet_id == request.wallet_id).first()
        
#         if not wallet or wallet.escrow_locked < request.amount_to_lock:
#             raise HTTPException(status_code=400, detail="Insufficient escrowed funds to release")

#         # Reverse the atomic move
#         wallet.escrow_locked -= request.amount_to_lock
#         wallet.spendable_balance += request.amount_to_lock
        
#         db.commit()
#         return {
#             "status": "success",
#             "released_amount": request.amount_to_lock,
#             "new_spendable": wallet.spendable_balance, 
#             "new_escrow": wallet.escrow_locked
#         }
#     finally:
#         db.close()