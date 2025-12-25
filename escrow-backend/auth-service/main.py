from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
import uuid

# --- Database Setup (cite: 1095) ---
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    wallet_id = Column(String, unique=True)
    otp_code = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BlueMint - Complete Auth & Integrity Service")

# --- Schemas (cite: 1313, 1310) ---
class IntegrityReport(BaseModel):
    device_id: str
    is_rooted: bool
    app_signature_valid: bool
    has_debugger: bool
    is_emulator: bool

class OTPRequest(BaseModel):
    phone: str

class VerifyRequest(BaseModel):
    phone: str
    otp: str

# --- API Endpoints ---

@app.post("/auth/request-otp")
async def request_otp(request: OTPRequest):
    """Simulates sending an OTP and creates a persistent user (cite: profile.html)."""
    db = SessionLocal()
    otp = str(random.randint(100000, 999999))
    user = db.query(User).filter(User.phone == request.phone).first()
    
    if not user:
        user = User(
            phone=request.phone, 
            wallet_id=f"WLT-{uuid.uuid4().hex[:8].upper()}",
            otp_code=otp
        )
        db.add(user)
    else:
        user.otp_code = otp
    
    db.commit()
    db.close()
    print(f"📡 [SMS GATEWAY] Sending OTP {otp} to {request.phone}")
    return {"message": "OTP sent successfully", "debug_otp": otp}

@app.post("/auth/verify-otp")
async def verify_otp(request: VerifyRequest):
    db = SessionLocal()
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user or user.otp_code != request.otp:
        db.close()
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    user.is_verified = True
    user.otp_code = None 
    db.commit()
    user_data = {"phone": user.phone, "wallet_id": user.wallet_id}
    db.close()
    return {"status": "success", "user": user_data}

@app.post("/auth/verify-integrity")
async def verify_integrity(report: IntegrityReport):
    """
    Mandatory endpoint called by Gateway.
    Implements 'Fail Closed' security posture.
    """
    # If any integrity check fails, return 'compromised'
    if report.is_rooted or not report.app_signature_valid or report.has_debugger:
        return {
            "status": "compromised",
            "message": "Security integrity check failed."
        }
    
    return {"status": "secure", "message": "Device verified."}

@app.get("/auth/profile/{wallet_id}")
async def get_profile(wallet_id: str):
    db = SessionLocal()
    user = db.query(User).filter(User.wallet_id == wallet_id).first()
    db.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"phone": user.phone, "wallet_id": user.wallet_id, "is_verified": user.is_verified}