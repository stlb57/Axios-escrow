**OFFLINE ESCROW WALLET SYSTEM – BACKEND**

This project is a microservice-based backend for a secure **offline payment system**.
It enables users to pay merchants via **Bluetooth**, without a real-time internet connection,
using **escrow-backed, cryptographically signed tokens**.

---

**SYSTEM OVERVIEW**

The system follows a **Value-Based model**, not a Balance-Based one.

- Funds are locked on the server
- Value is converted into **single-use tokens**
- Tokens represent a claim on locked money
- Tokens are exchanged **offline**
- Settlement happens **online**

This prevents double spending and ensures security even when devices are offline.

---

**CORE SERVICES**

**1. Identity & Auth Service (Port 8000)**  
Acts as the gatekeeper of the system.

Responsibilities:
- User identity management
- App integrity verification
- Integrity Gating (rooted/jailbroken device detection)

Compromised devices are **blocked from offline features**.

---

**2. Escrow & Wallet Service (Port 8001)**  
Manages balances and escrow vaults.

Responsibilities:
- Track spendable balance
- Lock funds for offline usage
- Prevent overspending

---

**3. Token Management Service (Port 8002)**  
Converts locked escrow into portable value.

Responsibilities:
- Mint fixed-denomination tokens
- Cryptographically sign tokens
- Ensure tokens are tamper-proof

---

**4. Settlement & Ledger Service (Port 8003)**  
Final monetary authority.

Responsibilities:
- Verify token authenticity
- Enforce single-use tokens
- Perform atomic settlement
- Credit merchant wallets

---

**PROJECT STRUCTURE**

escrow-backend/
├── .venv/                  # Python 3.12 virtual environment
├── auth-service/           # Identity & app integrity
├── escrow-service/         # Wallet & escrow vault
├── token-service/          # Token minting & signing
└── settlement-service/     # Ledger & settlement logic

---

**SETUP INSTRUCTIONS**

**Prerequisites**
- Python 3.12
- PowerShell (Windows)

---

**Environment Setup**

From the escrow-backend root directory:

python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn PyJWT pydantic

---

**RUNNING THE SERVICES**

Open four terminals, activate .venv in each, and run:

Auth Service:
uvicorn auth_service.main:app --reload --host 0.0.0.0 --port 8000

Escrow Service:
uvicorn escrow_service.main:app --reload --host 0.0.0.0 --port 8001

Token Service:
uvicorn token_service.main:app --reload --host 0.0.0.0 --port 8002

Settlement Service:
uvicorn settlement_service.main:app --reload --host 0.0.0.0 --port 8003

Note:
--host 0.0.0.0 allows external devices to connect via local IP.

---

**TESTING THE SERVICES**

Each service exposes a Swagger UI.

---

**Auth & Integrity Service**
URL: http://127.0.0.1:8000/docs

Test:
POST /auth/verify-integrity
{
  "is_rooted": true
}

Expected:
offline_mode_enabled = false

This confirms the system **fails closed** on compromised devices.

---

**Escrow Locking**
URL: http://127.0.0.1:8001/docs

Test:
POST /wallet/lock-escrow for ₹500

Expected:
- Spendable balance decreases
- Escrow locked amount increases

---

**Token Minting**
URL: http://127.0.0.1:8002/docs

Test:
POST /tokens/mint for locked ₹500

Expected:
- List of signed tokens
- Fixed denominations

---

**Atomic Settlement**
URL: http://127.0.0.1:8003/docs

Test:
POST /settle using token_id

Expected:
- First attempt: status = success
- Second attempt: failure (double-spending prevention)
