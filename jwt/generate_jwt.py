# generate_jwt.py
import jwt
import datetime
import time
import json
import uuid
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# --- Configuration (MUST match your JWTProvider and RouteAuthFilter) ---

# This MUST match the 'issuer' field in your JWTProvider.
# It's the unique identifier of who issued the token.
ISSUER = "https://my-local-issuer.example.com" # <--- IMPORTANT: Match JWTProvider's 'issuer' field

# This MUST match the audience you require in your RouteAuthFilter's verifyClaims.
AUDIENCE = "your-api-audience"

# This is a custom claim required by your RouteAuthFilter.
# Set to "admin" if your RouteAuthFilter checks for role: admin.
# If your RouteAuthFilter has no 'verifyClaims', you can set this to None or remove it from payload.
REQUIRED_ROLE = "admin"

# This MUST match the 'kid' (Key ID) from your generated JWKS and your JWTProvider.
# This helps the verifier select the correct public key if there are multiple.
KEY_ID = "847e1604-3665-44f2-8f4b-7a698ebfa926" # <--- IMPORTANT: Paste the KID from your generate_key_and_jwks.py output

# This MUST match the 'alg' (Algorithm) from your generated JWKS and your JWTProvider.
# E.g., "RS256", "RS512"
ALGORITHM = "RS512" # <--- IMPORTANT: Paste the ALG from your generate_key_and_jwks.py output

# Path to the private key file you generated using openssl
PRIVATE_KEY_FILE = "private_key.pem"

# --- Load Private Key ---
try:
    with open(PRIVATE_KEY_FILE, "rb") as f:
        private_key_pem = f.read()
    private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())
except FileNotFoundError:
    print(f"Error: Private key file '{PRIVATE_KEY_FILE}' not found.")
    print("Please ensure you've run 'openssl genrsa -out private_key.pem 2048' and 'openssl rsa -in private_key.pem -pubout -out public_key.pem'.")
    exit(1)
except Exception as e:
    print(f"Error loading private key: {e}")
    exit(1)


# --- Define Claims (JWT Payload) ---
current_time = int(time.time())

payload = {
    "sub": "testuser", # Subject of the JWT
    "iss": ISSUER,     # Issuer of the JWT
    "aud": [AUDIENCE], # Audience of the JWT (typically an array in JWT spec)
    "iat": current_time, # Issued At (valid from this time)
    "nbf": current_time, # Not Before (token is valid from this time)
    "exp": current_time + 3600, # Expiration (1 hour from now)
    "jti": str(uuid.uuid4()), # JWT ID (unique identifier for the token)
}

# Add custom claims if required by your RouteAuthFilter
if REQUIRED_ROLE:
    payload["role"] = REQUIRED_ROLE

# --- Define JWT Header ---
headers = {
    "alg": ALGORITHM,
    "typ": "JWT",
    "kid": KEY_ID # Key ID to indicate which key from the JWKS to use for verification
}


# --- Generate JWT ---
try:
    jwt_token = jwt.encode(
        payload,
        private_key,
        algorithm=ALGORITHM,
        headers=headers
    )
except Exception as e:
    print(f"Error generating JWT: {e}")
    exit(1)

#print("\n--- GENERATED JWT TOKEN ---")
print(jwt_token)
#print("\n--- DECODED PAYLOAD ---")
#print(json.dumps(payload, indent=2))
#print("\n--- DECODED HEADER ---")
#print(json.dumps(headers, indent=2))
