async function refreshMerchant() {
    const MERCHANT_ID = "MCH-CAFE-X"; // This must match your test_flow.py
    try {
        // Call the new GET endpoint we just created
        const response = await fetch(`http://localhost:8003/merchant/${MERCHANT_ID}/earnings`);
        const data = await response.json();
        
        if (data.total_earnings !== undefined) {
            // Update the UI with the real-time sum from the database
            document.getElementById('merchant-balance').innerText = `₹${data.total_earnings.toFixed(2)}`;
            document.getElementById('settlement-log').innerText = "Earnings synced with Ledger DB.";
        }
    } catch (err) {
        document.getElementById('settlement-log').innerText = "Sync Failed: Service Unreachable.";
    }
}

// Check for new payments every 3 seconds for the demo
setInterval(refreshMerchant, 3000);
window.onload = refreshMerchant;