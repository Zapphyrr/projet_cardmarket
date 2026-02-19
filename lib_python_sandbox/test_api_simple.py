import requests
import json

API_URL = "https://projetcardmarket-production.up.railway.app/"

print("=" * 60)
print("TEST SIMPLE API")
print("=" * 60)

# Test 1: Health check (GET)
print("\n1️⃣ Test GET /health...")
try:
    r = requests.get(f"{API_URL}/health", timeout=10)
    print(f"   ✅ Status: {r.status_code}")
    print(f"   📦 Response: {r.json()}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 2: Search avec image minimale (POST)
print("\n2️⃣ Test POST /search...")
try:
    # Image 1x1 pixel en base64
    tiny_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    payload = {"image": tiny_image}
    headers = {"Content-Type": "application/json"}
    
    print(f"   📤 Envoi de la requête...")
    r = requests.post(
        f"{API_URL}/search",
        json=payload,
        headers=headers,
        timeout=60
    )
    print(f"   ✅ Status: {r.status_code}")
    print(f"   📦 Response: {r.text[:200]}")
except requests.exceptions.Timeout:
    print(f"   ⏱️  TIMEOUT après 60s")
except requests.exceptions.ConnectionError as e:
    print(f"   ❌ Erreur connexion: {e}")
except Exception as e:
    print(f"   ❌ Erreur: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
