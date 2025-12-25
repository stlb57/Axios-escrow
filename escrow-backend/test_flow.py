import httpx
import asyncio
import uuid

async def run_valid_flow():
    GATEWAY_URL = "http://localhost:8080/gateway/prepare-offline"
    SETTLE_URL = "http://localhost:8003/settle"
    WALLET_ID = "WLT-8F3A-92KD"

    async with httpx.AsyncClient() as client:
        # STEP 1: LOCK MONEY & GET VALID TOKENS
        print(f"--- 1. Locking ₹500 from {WALLET_ID} ---")
        lock_payload = {
            "wallet_id": WALLET_ID,
            "phone": "919876543210",
            "amount": 500.0,
            "integrity_report": {
                "device_id": "demo_device",
                "is_rooted": False, # Capitalized
                "app_signature_valid": True, # Capitalized
                "has_debugger": False, # Capitalized
                "is_emulator": False  # Capitalized
            }
        }
        
        resp = await client.post(GATEWAY_URL, json=lock_payload)
        lock_data = resp.json()
        
        if "tokens" not in lock_data:
            print(f"FAILED TO LOCK: {lock_data}")
            return

        valid_tokens = lock_data["tokens"]
        print(f"SUCCESS: Received {len(valid_tokens)} cryptographically signed tokens.")

        # STEP 2: SETTLE (PAY) USING THE VALID TOKENS
        print("\n--- 2. Settling Tokens (Receiver connects to Internet) ---")
        settle_payload = {
            "merchant_id": "MCH-CAFE-X",
            "payment_request_id": f"FINAL-DEMO-{uuid.uuid4().hex[:6]}",
            "tokens": valid_tokens 
        }
        
        settle_resp = await client.post(SETTLE_URL, json=settle_payload)
        print(f"SETTLEMENT RESULT: {settle_resp.json()}")

if __name__ == "__main__":
    asyncio.run(run_valid_flow())