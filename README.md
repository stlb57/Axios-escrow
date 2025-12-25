
---

# **🚀 BlueMint: Offline Escrow Wallet System**

**BlueMint** is a high-performance, microservice-based backend designed to enable **secure, offline user-to-merchant payments**. It solves the "Double Spend" problem in no-internet environments by using **Server-Authoritative Escrow** and **Cryptographically Signed Bearer Tokens**.

---

## **📁 Project Folder Structure**

```text
axios-escrow/
├── 📂 escrow-backend/
│   ├── 📂 auth-service/         # Identity & Device Integrity Gating
│   ├── 📂 escrow-service/       # Fund Locking & Vault Management
│   ├── 📂 token-service/        # Ed25519 Token Minting
│   ├── 📂 settlement-service/   # Atomic Ledger & Payment Finality
│   ├── 📂 transaction-service/  # History & Dashboard API
│   ├── 📂 risk-service/         # Dynamic Limits & Anomaly Detection
│   ├── 📂 admin-service/        # Dispute Resolution & Auditing
│   ├── 📂 gateway-service/      # API Orchestration (Entry Point)
│   └── 📂 shared/               # Shared Security & Crypto Utilities
├── 📂 escrow-wallet/            # Android UI (HTML Prototype)
├── 📄 .gitignore                # Environment protection
└── 📄 README.md                 # Project Documentation

```

---

## **🛠 Service-Wise Summary**

| Service | Port | **Core Responsibility** | **Key DevOps Feature** |
| --- | --- | --- | --- |
| **Auth** | `8000` | Gating access based on **Device Integrity** (Root/Debugger checks). | Fail-closed security posture. |
| **Escrow** | `8001` | Moving spendable balance into a **Server-Locked Vault**. | Enforces strict ₹5,000 risk cap. |
| **Token** | `8002` | Minting **Ed25519 signed payloads** for offline use. | Fixed-denomination fraud prevention. |
| **Settlement** | `8003` | The **Final Authority**; moves real money to merchants. | Idempotent transaction handling. |
| **Transaction** | `8004` | Aggregating "Pending" vs "Settled" states for UI. | Multi-service data projection. |
| **Risk** | `8005` | Dynamic configuration of system limits and expiry. | Hot-swappable business rules. |
| **Admin** | `8006` | Forensic audit tools for dispute resolution. | Immutable ledger reconstruction. |
| **Gateway** | `8080` | **Orchestrator**; one call handles the entire offline setup. | Service-mesh traffic management. |

---

## **⚙️ Setup & Installation**

**1. Create the Environment**

```powershell
# Use Python 3.12 to create the venv
python -m venv .venv

# Activate the venv
.\.venv\Scripts\Activate.ps1

```

**2. Install Requirements**

```powershell
# Install FastAPI, Cryptography, and Async HTTP tools
pip install fastapi uvicorn PyJWT pydantic pynacl httpx

```

---

## **🧪 Testing Commands**

To test the system flawlessly, run each service in a separate terminal window:

**Step 1: Start the Gateway (The Entry Point)**

```powershell
cd escrow-backend/gateway-service
uvicorn main:app --reload --host 0.0.0.0 --port 8080

```

**Step 2: Start Supporting Services**

* **Auth:** `uvicorn auth-service.main:app --port 8000`
* **Escrow:** `uvicorn escrow-service.main:app --port 8001`
* **Token:** `uvicorn token-service.main:app --port 8002`
* **Settlement:** `uvicorn settlement-service.main:app --port 8003`

**Step 3: Run the End-to-End Test**

1. Open your browser to **`http://127.0.0.1:8080/docs`**.
2. Locate the **`POST /gateway/prepare-offline`** endpoint.
3. Execute with this **JSON Payload**:

```json
{
  "wallet_id": "WLT-8F3A-92KD",
  "phone": "919876543210",
  "amount": 500.0,
  "integrity_report": {
    "device_id": "android_001",
    "is_rooted": false,
    "app_signature_valid": true,
    "has_debugger": false,
    "is_emulator": false
  }
}

```

---

## **🔐 Core Security Invariants**

**1. Authority Separation**
The Android app is **never** trusted to calculate its own balance. It only carries "Claims" (Tokens) which the **Settlement Service** validates against the **Escrow Vault**.

**2. Cryptographic Sealing**
Every token is signed with an **Ed25519 Private Key**. If a hacker modifies a single bit of the token (e.g., changing ₹100 to ₹1000), the signature check fails immediately.

**3. Idempotency Guard**
The **Settlement Service** tracks `payment_request_id`. If a merchant's app retries a payment due to a bad network, the backend recognizes the ID and ensures **zero duplicate charges**.

**4. Integrity Gating**
Offline mode is a "High-Privilege" state. The **Auth Service** verifies the Android device's health before the **Gateway** allows money to be moved into Escrow.

---

## **📱 Android UI Integration**

* **`index.html`**: Connects to Port `8004` to show the "Pending" status of offline tokens.
* **`pay.html` / `receive.html**`: These represent the Bluetooth handshake where Token JSONs are transferred.
* **`profile.html`**: Connects to Port `8000` to show the "Security Integrity" status of the device.

---

**"This system is intentionally designed to assume the network is broken, the device is hostile, and the transport is public—yet the money remains mathematically safe."**