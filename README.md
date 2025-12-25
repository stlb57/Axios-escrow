

---

# **🚀 BlueMint: Detailed Project Specification**

**BlueMint** is a secure, microservice-based fintech platform designed for **User-to-Merchant (U2M)** payments in environments without internet connectivity. It utilizes **Server-Authoritative Escrow**, **Ed25519 Cryptographic Signing**, and **Idempotent Settlement** to ensure that money remains mathematically safe, even when the device is offline.

---

## **📁 1. Project Architecture & Ports**

Each service is a self-contained FastAPI application with its own persistent SQLite database.

| Service | Port | Database | Core Responsibility |
| --- | --- | --- | --- |
| **Auth** | `8000` | `users.db` | Identity, OTP verification, and **Device Integrity Gating**. |
| **Escrow** | `8001` | `wallets.db` | Managing spendable balances and the **Locked Offline Vault**. |
| **Token** | `8002` | *In-Memory* | Minting **Ed25519-signed** bearer tokens in fixed denominations. |
| **Settlement** | `8003` | `ledger.db` | Verifying signatures, preventing **Double Spending**, and updating merchant earnings. |
| **Transaction** | `8004` | *Internal* | Aggregating history and pending settlement status for the UI. |
| **Risk** | `8005` | *Config* | Enforcing global limits (e.g., ₹5,000 cap) and anomaly detection. |
| **Admin** | `8006` | *Audit* | Providing forensic audit trails for dispute resolution. |
| **Gateway** | `8080` | *None* | **Orchestrator**: Single entry point that handles the entire locking/minting flow. |

---

## **🔄 2. The Fundamental Offline Loop**

The system follows a strict three-phase security protocol:

1. **Phase 1: Pre-Locking (Online)** The user moves money from their **Spendable Balance** to an **Escrow Locked** state. The system issues a JSON bundle of cryptographically signed tokens representing that specific value.
2. **Phase 2: The Transfer (Offline)** The User App sends the signed JSON tokens to the Merchant App via **Bluetooth Low Energy (BLE)**. The merchant verifies the signature offline using the server's public key.
3. **Phase 3: Settlement (Online)** The merchant connects to the internet and uploads the JSON tokens to the **Settlement Service**. The service verifies the signature one final time, credits the merchant's ledger, and calls the **Escrow Service** to "burn" (remove) the funds from the user's locked vault.

---

## **🛠 3. Setup & Environment**

### **Initial Installation**

```powershell
# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install core dependencies
pip install fastapi uvicorn pydantic sqlalchemy pynacl httpx

```

---

## **💻 4. Execution Commands (Start Every Service)**

Open a separate terminal window for each service. **Run all commands from the `escrow-backend` root folder** to ensure database paths are consistent.

1. **Gateway:** `uvicorn gateway-service.main:app --reload --host 0.0.0.0 --port 8080`
2. **Auth:** `uvicorn auth-service.main:app --reload --port 8000`
3. **Escrow:** `uvicorn escrow-service.main:app --reload --port 8001`
4. **Token:** `uvicorn token-service.main:app --reload --port 8002`
5. **Settlement:** `uvicorn settlement-service.main:app --reload --port 8003`
6. **Transaction:** `uvicorn transaction-service.main:app --reload --port 8004`
7. **Risk:** `uvicorn risk-service.main:app --reload --port 8005`
8. **Admin:** `uvicorn admin-service.main:app --reload --port 8006`

---

## **🧪 5. Testing the Full Lifecycle**

### **Step 1: Admin Top-Up (₹50,000)**

Before testing, add funds to your account via the Swagger UI:

* URL: `http://localhost:8001/docs`
* Endpoint: `POST /wallet/admin/topup`
* JSON: `{"wallet_id": "WLT-8F3A-92KD", "amount": 50000.0}`

### **Step 2: The User Interface**

* **User Dashboard:** Open `http://localhost:8080/app/index.html`.
* **Merchant Terminal:** Open `http://localhost:8080/app/merchant.html`.

### **Step 3: Simulate Payment (End-to-End)**

Run the provided `test_flow.py` script to lock new funds and settle them:

```powershell
python test_flow.py

```

* **Observation:** The User Dashboard will show the **Spendable Balance** decrease, while the **Merchant Terminal** shows an increase in earnings. Because the funds are "burned" upon settlement, the **Locked Balance** will return to ₹0.

---

## **🔐 6. Core Security Invariants**

* **Ed25519 Signing:** Every token is signed with a server-side private key using the format `{id}|{wallet}|{value}|{expiry}`.
* **Double-Spend Prevention:** The `spent_tokens` table in the settlement database ensures no token ID is ever processed twice.
* **Integrity Gating:** The **Auth Service** rejects any requests from devices that are rooted, have a debugger attached, or are running in an emulator.
* **Idempotency:** The `payment_request_id` prevents a merchant from accidentally charging a user twice for the same transaction due to network retries.

---

**"BlueMint assumes the device is hostile and the network is unreliable. Security is handled by the math, not the connection."**
