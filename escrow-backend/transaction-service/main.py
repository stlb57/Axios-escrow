from fastapi import FastAPI, HTTPException
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Offline Escrow - Transaction & History Service")

# --- Mock Data ---
# In production, this service would query the Settlement and Token services.
# Linking to the Wallet ID: WLT-8F3A-92KD (Rajesh Kumar)
mock_transactions = [
    {
        "id": "TXN-2512-449AF",
        "wallet_id": "WLT-8F3A-92KD",
        "name": "CafeX Store",
        "amount": -450.00,
        "type": "payment",
        "status": "pending", # cite: transaction-result.html
        "timestamp": "2025-12-25T14:30:00",
        "method": "Bluetooth"
    },
    {
        "id": "TXN-2412-882BB",
        "wallet_id": "WLT-8F3A-92KD",
        "name": "Priya Sharma",
        "amount": 1200.00,
        "type": "receive",
        "status": "settled",
        "timestamp": "2025-12-24T08:45:00",
        "method": "QR Code"
    },
    {
        "id": "TXN-2012-111CC",
        "wallet_id": "WLT-8F3A-92KD",
        "name": "Added balance",
        "amount": 2000.00,
        "type": "topup",
        "status": "settled",
        "timestamp": "2025-12-20T10:15:00",
        "method": "Bank"
    }
]

# --- API Endpoints ---

@app.get("/transactions/{wallet_id}")
async def get_all_transactions(wallet_id: str):
    """Powers the All Transactions screen (cite: transactions.html)."""
    user_txs = [tx for tx in mock_transactions if tx["wallet_id"] == wallet_id]
    return user_txs

@app.get("/history/{wallet_id}")
async def get_settled_history(wallet_id: str):
    """Powers the History screen (Settled Transactions Only) (cite: history.html)."""
    user_history = [tx for tx in mock_transactions if tx["wallet_id"] == wallet_id and tx["status"] == "settled"]
    return user_history

@app.get("/status/{wallet_id}")
async def get_dashboard_status(wallet_id: str):
    """Powers the Status cards on the Home screen (cite: index.html)."""
    user_txs = [tx for tx in mock_transactions if tx["wallet_id"] == wallet_id]
    
    pending_count = len([tx for tx in user_txs if tx["status"] == "pending"])
    incoming_total = sum([tx["amount"] for tx in user_txs if tx["type"] == "receive" and tx["status"] == "pending"])
    
    return {
        "pending_settlements": pending_count,
        "incoming_amount": incoming_total,
        "currency": "INR"
    }