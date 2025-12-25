import nacl.signing
import nacl.encoding

# In a real app, generate once and save securely
# seed = secrets.token_bytes(32)
# private_key = nacl.signing.SigningKey(seed)

# For this demo, we'll use a fixed seed so the keys remain consistent
MOCK_SEED = b"seven_secret_seeds_for_escrow_v1"
private_key = nacl.signing.SigningKey(MOCK_SEED)
public_key = private_key.verify_key

def sign_token_data(data: str) -> str:
    """Signs token data using the server's private key (cite: 3051, 3636)."""
    signed = private_key.sign(data.encode('utf-8'))
    return signed.signature.hex()

def verify_token_signature(data: str, signature_hex: str) -> bool:
    """Verifies a token using the server's public key (cite: 3654, 4421)."""
    try:
        sig = bytes.fromhex(signature_hex)
        public_key.verify(data.encode('utf-8'), sig)
        return True
    except Exception:
        return False