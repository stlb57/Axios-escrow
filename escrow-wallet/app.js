const WALLET_ID = "WLT-8F3A-92KD"; // Use the one generated during your OTP test

async function updateDashboard() {
    try {
        const response = await fetch(`http://localhost:8001/wallet/${WALLET_ID}/balance`);
        const data = await response.json();
        document.getElementById('balance-amount').innerText = `₹${data.spendable_balance}`;
        document.getElementById('escrow-locked-amount').innerText = `₹${data.escrow_locked}`;
        document.getElementById('status-message').innerText = "Dashboard updated from SQLite.";
    } catch (err) {
        document.getElementById('status-message').innerText = "Error connecting to Escrow Service.";
    }
}

async function prepareOffline() {
    document.getElementById('status-message').innerText = "Requesting Gateway...";
    try {
        const response = await fetch('http://localhost:8080/gateway/prepare-offline', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                wallet_id: WALLET_ID,
                phone: "919876543210",
                amount: 500.0,
                integrity_report: {
                    device_id: "web_browser_test",
                    is_rooted: false,
                    app_signature_valid: true,
                    has_debugger: false,
                    is_emulator: false
                }
            })
        });
        const data = await response.json();
        if (data.status === "ready") {
            document.getElementById('status-message').innerText = "Tokens Minted! Check Token Terminal.";
            updateDashboard(); // Refresh balance after locking
        }
    } catch (err) {
        document.getElementById('status-message').innerText = "Gateway Connection Failed.";
    }
}

// Initial Load
window.onload = updateDashboard;