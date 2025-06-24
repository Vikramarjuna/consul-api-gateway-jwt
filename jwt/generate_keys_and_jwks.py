# generate_keys_and_jwks.py
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwcrypto.jwk import JWK
import json
import uuid
import base64
import os

# --- Configuration for Key Generation and JWKS ---
ALGORITHM = "RS512" # Algorithm for signing JWTs (e.g., "RS256", "RS512")
KEY_ID = str(uuid.uuid4()) # Unique Key ID for the JWKS
KEY_SIZE = 2048 # RSA key size (2048 bits is common)

PRIVATE_KEY_FILE = "private_key.pem"
PUBLIC_KEY_FILE = "public_key.pem"

# --- 1. Generate RSA Private and Public Keys ---
print(f"--- Generating {KEY_SIZE}-bit RSA key pair... ---")
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=KEY_SIZE
)
print("Key pair generated.")

# --- 2. Save Private Key to PEM File ---
try:
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption() # This is correct for private key
        ))
    print(f"Private key saved to {PRIVATE_KEY_FILE}")
except IOError as e:
    print(f"Error saving private key to file: {e}")
    exit(1)

# --- 3. Save Public Key to PEM File ---
try:
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
            # REMOVED encryption_algorithm=serialization.NoEncryption() HERE <--- THIS IS THE FIX
        ))
    print(f"Public key saved to {PUBLIC_KEY_FILE}")
except IOError as e:
    print(f"Error saving public key to file: {e}")
    exit(1)

# --- 4. Convert Public Key to JWKS Format ---
print("\n--- Converting Public Key to JWKS format... ---")
# Load from the saved PEM file for robust practice, though can use public_key object directly
with open(PUBLIC_KEY_FILE, "rb") as f:
    public_key_pem_loaded = f.read()
public_key_jwk = JWK.from_pem(public_key_pem_loaded)

# Export the JWK object as a dictionary
public_key_jwk_dict = public_key_jwk.export(as_dict=True)

# Add common JWKS fields required for JWT verification
public_key_jwk_dict["use"] = "sig" # For signature verification
public_key_jwk_dict["alg"] = ALGORITHM # Algorithm used for signing
public_key_jwk_dict["kid"] = KEY_ID # Unique Key ID (important for key rotation)

# Prepare JWKS set
jwks_set = {"keys": [public_key_jwk_dict]}

# --- 5. Print JWKS and Base64-Encoded JWKS ---
print("\n--- JWKS Public Key JSON (for review) ---")
print(json.dumps(jwks_set, indent=2))

jwks_json_string = json.dumps(jwks_set)
jwks_base64_encoded = base64.b64encode(jwks_json_string.encode('utf-8')).decode('utf-8')
print("\n--- BASE64-ENCODED JWKS STRING (Copy this for JWTProvider.jsonWebKeySet.local.jwks) ---")
print(jwks_base64_encoded)


print(f"\n--- IMPORTANT: Note your KID: {public_key_jwk_dict['kid']} ---")
print(f"--- IMPORTANT: Note your ALG: {public_key_jwk_dict['alg']} ---")
