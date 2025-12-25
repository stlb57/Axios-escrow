Offline Escrow Wallet System - Backend
This project is a microservice-based backend for a secure offline payment system. It enables users to pay merchants via Bluetooth without a real-time internet connection by using escrow-backed, cryptographically signed tokens.


System Overview
The system architecture follows a "Value-Based" rather than "Balance-Based" model. Value is materialized as server-authorized tokens that act as single-use claims on locked funds.



The 4 Core Services
Identity & Auth Service (Port 8000): Acts as the gatekeeper. It manages user profiles and enforces Integrity Gating, ensuring that compromised (rooted) devices cannot access offline features.

Escrow & Wallet Service (Port 8001): Manages the user's spendable balance and handles Escrow Locking, moving funds into a reserved state for offline use.


Token Management Service (Port 8002): Converts locked escrow into portable, fixed-denomination digital tokens signed by the server.




Settlement & Ledger Service (Port 8003): The final monetary authority. It verifies tokens and performs Atomic Settlement, moving money to the merchant's wallet.





Project Structure
Plaintext

escrow-backend/
├── .venv/                  # Python 3.12 virtual environment
├── auth-service/           # Identity, App Integrity, and Profile management
├── escrow-service/         # Wallet balance and Escrow vault management
├── token-service/          # Token minting and signing logic
└── settlement-service/     # Atomic ledger and merchant payment logic
Setup Instructions
Prerequisites
Python 3.12: Recommended for performance and async support.

PowerShell: For running the setup commands on Windows.

1. Environment Setup
From the escrow-backend root folder, run:

PowerShell

# Create the virtual environment
python -m venv .venv

# Allow script execution for the session
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activate the environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install fastapi uvicorn PyJWT pydantic
Running the Services
Open four separate terminal windows, activate the .venv in each, and run the following commands:

Auth Service: uvicorn auth_service.main:app --reload --host 0.0.0.0 --port 8000

Escrow Service: uvicorn escrow_service.main:app --reload --host 0.0.0.0 --port 8001

Token Service: uvicorn token_service.main:app --reload --host 0.0.0.0 --port 8002

Settlement Service: uvicorn settlement_service.main:app --reload --host 0.0.0.0 --port 8003

Note: The --host 0.0.0.0 flag allows external devices (like an Android phone or emulator) to connect via your laptop's local IP address.

Testing the Services
Each service includes an interactive Swagger UI accessible via your browser.

1. Auth & Integrity (Port 8000)
URL: http://127.0.0.1:8000/docs

Test: Send a POST to /auth/verify-integrity with "is_rooted": true.

Expect: offline_mode_enabled should be false. This proves the system "fails closed" on compromised devices.

2. Escrow Locking (Port 8001)
URL: http://127.0.0.1:8001/docs

Test: Send a POST to /wallet/lock-escrow for ₹500.


Expect: spendable_balance should decrease and escrow_locked should increase.

3. Token Minting (Port 8002)
URL: http://127.0.0.1:8002/docs

Test: Send a POST to /tokens/mint for the ₹500 you locked.


Expect: A list of cryptographically signed tokens in fixed denominations.



4. Atomic Settlement (Port 8003)
URL: http://127.0.0.1:8003/docs

Test: Send a POST to /settle using a token_id from the previous step.

Expect: status: "success" on the first try. A second attempt with the same token must fail (Double-spending protection).