import httpx
import asyncio
import uuid # Add this import

async def run_test():
    GATEWAY_URL = "http://localhost:8080/gateway/prepare-offline"
    SETTLE_URL = "http://localhost:8003/settle"

    print("--- 1. Requesting Offline Tokens via Gateway ---")
    payload = {
        "wallet_id": "WLT-8F3A-92KD", # Ensure this matches your index.html wallet
        "phone": "919876543210",
        "amount": 500.0,
        "integrity_report": {
            "device_id": "mock_device_001",
            "is_rooted": False,
            "app_signature_valid": True,
            "has_debugger": False,
            "is_emulator": False
        }
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(GATEWAY_URL, json=payload)
        data = resp.json()
        tokens = data["tokens"]
        print(f"SUCCESS: Received {len(tokens)} tokens.")

        print("\n--- 2. Simulating Settlement ---")
        settle_payload = {
            "merchant_id": "MCH-CAFE-X",
            # CHANGE: Generate a unique ID so it's not 'already_settled'
            "payment_request_id": f"ORDER-{uuid.uuid4().hex[:8]}", 
            "tokens": tokens 
        }
        
        settle_resp = await client.post(SETTLE_URL, json=settle_payload)
        print(f"SETTLEMENT RESULT: {settle_resp.json()}")

if __name__ == "__main__":
    asyncio.run(run_test())