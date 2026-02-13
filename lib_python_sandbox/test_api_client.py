import requests
import base64
import json
import time

# URL du serveur API
# En local : http://localhost:5000
# En production : https://votre-app.onrender.com
API_URL = "http://localhost:5000"

def test_health():
    """Test si le serveur est accessible"""
    print("🔍 Test de connexion au serveur...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Serveur OK ! {data['cartes_loaded']} cartes chargées")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Impossible de contacter le serveur: {e}")
        print("\n💡 Assurez-vous que api_server.py tourne avec:")
        print("   python api_server.py")
        return False

def search_card(image_path):
    """Envoie une image au serveur et affiche le résultat"""
    print(f"\n📤 Envoi de l'image: {image_path}")
    
    try:
        # 1. Lire l'image et la convertir en base64
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        print(f"   Taille image: {len(image_bytes) / 1024:.1f} Ko")
        
        # 2. Envoyer la requête
        t_start = time.time()
        response = requests.post(
            f"{API_URL}/search",
            json={'image': image_base64},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        t_end = time.time()
        
        print(f"⏱️  Temps de réponse: {t_end - t_start:.2f}s")
        
        # 3. Traiter la réponse
        if response.status_code == 200:
            data = response.json()
            print("\n✅ CARTE TROUVÉE !")
            print("="*50)
            print(f"📋 Carte: {data['carte']}")
            print(f"🔢 Numéro: {data['numero']}")
            print(f"📛 Nom: {data['nom']}")
            print(f"📦 Set: {data['set_name']}")
            print(f"🎯 Score: {data['score']}")
            print(f"🔗 Matches: {data['matches_count']}")
            print("="*50)
            return data
        
        elif response.status_code == 404:
            data = response.json()
            print(f"\n❌ {data.get('error', 'Carte non trouvée')}")
            return None
        
        else:
            print(f"\n❌ Erreur serveur: {response.status_code}")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    print("="*50)
    print("🧪 TEST DE L'API DE RECONNAISSANCE")
    print("="*50)
    
    # 1. Test de connexion
    if not test_health():
        exit(1)
    
    # 2. Test avec une image
    # Changez le chemin vers votre image de test
    image_test = "templates/locklass.png"
    
    print(f"\n📸 Test avec: {image_test}")
    result = search_card(image_test)
    
    if result:
        print("\n🎉 Test réussi !")
    else:
        print("\n⚠️  Test échoué")
