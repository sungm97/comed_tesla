#!/usr/bin/env python3
"""
Tesla Fleet Auth & Vehicle List (Direct REST)

This script exchanges your Fleet refresh token for an access token
and then fetches the list of vehicles via the Partner endpoint.

Requirements (inside your venv):
    pip install requests python-dotenv

.env (in the same directory, NO inline comments):
    TESLA_CLIENT_ID=5e0c3e11-8c46-4ee0-afc4-ba7f24e7e910
    TESLA_CLIENT_SECRET=ta-secret.pTE@4K$-PO!dG58d
    TESLA_REFRESH_TOKEN=eyJhbGciOiJIUzI1NiJ9...   # Fleet refresh token
    TESLA_API_HOST=https://YOUR_REGION_SPECIFIC_HOST

Run:
    python auth_only.py
"""
import os, sys, json, base64
import requests
from dotenv import load_dotenv

# ──── Load environment ────────────────────────────────────────────────
load_dotenv()
CLIENT_ID     = os.getenv("TESLA_CLIENT_ID")
CLIENT_SECRET = os.getenv("TESLA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("TESLA_REFRESH_TOKEN")
API_HOST_ENV  = os.getenv("TESLA_API_HOST")

if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    sys.exit("❌  .env must include TESLA_CLIENT_ID, TESLA_CLIENT_SECRET, TESLA_REFRESH_TOKEN")

# ──── Determine API_HOST ────────────────────────────────────────────
if API_HOST_ENV:
    API_HOST = API_HOST_ENV
    print(f"🚧  Using API_HOST from .env: {API_HOST}")
else:
    try:
        _, payload_b64, _ = REFRESH_TOKEN.split('.')
        padded = payload_b64 + '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        API_HOST = payload.get('iss')
        if not API_HOST or not API_HOST.startswith('https://'):
            raise ValueError
        print(f"🚧  Using API_HOST from token payload: {API_HOST}")
    except Exception:
        sys.exit("❌  Could not derive API_HOST. Set TESLA_API_HOST in .env.")

# ──── Exchange refresh token for access token ────────────────────────
TOKEN_URL = "https://auth.tesla.com/oauth2/v3/token"
headers   = {"Content-Type": "application/x-www-form-urlencoded"}
data      = {
    "grant_type":    "refresh_token",
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN,
    "audience":      API_HOST,
}

print("🔑  Exchanging refresh token for access token…")
response = requests.post(TOKEN_URL, headers=headers, data=data)
if not response.ok:
    sys.exit(f"❌  Auth error {response.status_code}: {response.text}")

tokens = response.json()
access_token = tokens.get("access_token")
if not access_token:
    sys.exit(f"❌  No access_token in response: {tokens}")

print(f"✅  Access token obtained (expires_in {tokens.get('expires_in')}s)")

# ──── Fetch vehicle list via Partner endpoint ───────────────────────
VEH_LIST_URL = f"{API_HOST}/api/1/partners/{CLIENT_ID}/vehicles"
print("🚗  Fetching vehicle list via partner endpoint…")
resp = requests.get(VEH_LIST_URL, headers={"Authorization": f"Bearer {access_token}"})
if not resp.ok:
    sys.exit(f"❌  Vehicle list error {resp.status_code}: {resp.text}")

vehicles = resp.json().get("response", [])
print("🚗  Vehicles found:")
print(json.dumps([
    {"id": v.get("id"), "vin": v.get("vin"), "name": v.get("display_name"), "state": v.get("state")} 
    for v in vehicles
], indent=2))
