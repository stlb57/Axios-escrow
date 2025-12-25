import httpx
import asyncio

async def run_test():
    # 1. Gateway URL (Port 8080)
    GATEWAY_URL = "http://localhost:8080/gateway/prepare-offline"
    # 2. Settlement URL (Port 8003)
    SETTLE_URL = "http://localhost:8003/settle"

    print("--- 1. Requesting Offline Tokens via Gateway ---")
    payload = {
        "wallet_id": "WLT-8F3A-92KD",
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
        # Step A: Get Tokens from Gateway
        resp = await client.post(GATEWAY_URL, json=payload)
        if resp.status_code != 200:
            print(f"FAILED: {resp.text}")
            return
        
        data = resp.json()
        tokens = data["tokens"]
        print(f"SUCCESS: Received {len(tokens)} tokens.")

        # Step B: Simulate "Spending" tokens at a Merchant (Settlement)
        print("\n--- 2. Simulating Settlement (Merchant cashing in) ---")
        settle_payload = {
            "merchant_id": "MCH-CAFE-X",
            "payment_request_id": "MOCK-ORDER-001",
            "tokens": tokens # Send the real tokens with signatures
        }
        
        settle_resp = await client.post(SETTLE_URL, json=settle_payload)
        print(f"SETTLEMENT RESULT: {settle_resp.json()}")

if __name__ == "__main__":
    asyncio.run(run_test())