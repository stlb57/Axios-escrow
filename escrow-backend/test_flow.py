import httpx
import asyncio
import uuid

async def run_settlement_flow():
    TOKEN_LIST_URL = "http://localhost:8002/tokens/wallet/WLT-8F3A-92KD"
    SETTLE_URL = "http://localhost:8003/settle"
    WALLET_ID = "WLT-8F3A-92KD"

    async with httpx.AsyncClient() as client:
        print(f"--- 1. Searching for existing tokens for {WALLET_ID} ---")
        try:
            token_resp = await client.get(TOKEN_LIST_URL)
            
            # Check if the service returned a valid status code
            if token_resp.status_code != 200:
                print(f"❌ ERROR: Token service returned status {token_resp.status_code}")
                return

            existing_tokens = token_resp.json()
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Could not talk to Token Service. Is it running on 8002? \n{e}")
            return

        if not existing_tokens:
            print(f"❌ NO TOKENS FOUND: You need to 'Lock Money' in the UI first while the service is running.")
            return

        print(f"✅ FOUND: {len(existing_tokens)} tokens ready for settlement.")

        print("\n--- 2. Settling Existing Tokens (Burning Locked Balance) ---")
        settle_payload = {
            "merchant_id": "MCH-CAFE-X",
            "payment_request_id": f"SETTLE-EXISTING-{uuid.uuid4().hex[:6]}",
            "tokens": existing_tokens 
        }
        
        settle_resp = await client.post(SETTLE_URL, json=settle_payload)
        result = settle_resp.json()
        
        if result.get("status") == "success":
            print(f"🚀 SUCCESS: Settled ₹{result['amount_settled']}.")
            print("Check your dashboard: Locked Balance should now be ₹0.00")
        else:
            print(f"Settlement Failed: {result}")

if __name__ == "__main__":
    asyncio.run(run_settlement_flow())