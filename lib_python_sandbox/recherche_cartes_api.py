import requests
import base64
import webbrowser
import urllib.parse
import time

# ========== CONFIGURATION ==========
# URL de votre API Railway déployée
API_URL = "https://projectcardmarket-production.up.railway.app"

# Configuration des headers pour Cardmarket
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

def trouver_carte_via_api(chemin_photo):
    """
    Envoie l'image à l'API Render et retourne les infos de la carte
    Plus besoin de charger orb_db.pkl ni de faire les calculs localement !
    """
    print(f"📤 Envoi de l'image à l'API: {chemin_photo}")
    t_start = time.time()
    
    try:
        # 1. Lire l'image et la convertir en base64
        with open(chemin_photo, 'rb') as f:
            image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        print(f"   Taille: {len(image_bytes) / 1024:.1f} Ko")
        
        # 2. Envoyer à l'API
        response = requests.post(
            f"{API_URL}/search",
            json={'image': image_base64},
            headers={'Content-Type': 'application/json'},
            timeout=60  # Augmenté à 60s pour Railway
        )
        
        t_end = time.time()
        print(f"⏱️  Temps total (réseau + traitement): {t_end - t_start:.2f}s")
        
        # 3. Traiter la réponse
        if response.status_code == 200:
            data = response.json()
            return {
                "carte": data['carte'],
                "carte_infos": {
                    "numero": data['numero'],
                    "nom": data['nom'],
                    "set_name": data['set_name']
                },
                "score": data['score'],
                "temps": round(t_end - t_start, 4)
            }
        elif response.status_code == 404:
            print("❌ Carte non trouvée par l'API")
            return None
        else:
            print(f"❌ Erreur serveur: {response.status_code}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Impossible de contacter le serveur API")
        print("💡 Vérifiez que api_server.py tourne ou que l'URL Render est correcte")
        return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def ouvrir_cardmarket_precis(nom, numero):
    """Ouvre Cardmarket avec le nom et numéro de la carte"""
    nom = nom.lower().replace("-", " ").strip()
    numero_propre = numero.split("/")[0]
    
    recherche = f"{nom} {numero}"
    query_encoded = urllib.parse.quote(recherche)
    url_recherche = f"https://www.cardmarket.com/fr/Pokemon/Products/Search?searchString={query_encoded}"

    try:
        session = requests.Session()
        response = session.get(url_recherche, headers=headers, timeout=15)
        url_finale = response.url
        
        if "/Search" in url_finale:
            print("⚠️ Pas de redirection automatique (Plusieurs résultats trouvés).")
            url_finale = url_finale + "&language=2"
        else:
            print("✅ Redirection réussie vers la carte !")
            url_propre = url_finale.split('?')[0]
            url_finale = url_propre + "?language=2"
        
        webbrowser.open(url_finale)
        
    except requests.RequestException as e:
        print(f"Erreur lors de la requête : {e}")

# ========== TEST ==========
if __name__ == "__main__":
    print("="*60)
    print("🔍 RECHERCHE DE CARTE VIA API")
    print("="*60)
    print(f"🌐 Serveur API: {API_URL}\n")
    
    # Test connexion API
    print("🔍 Vérification de la connexion...")
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        if health.status_code == 200:
            data = health.json()
            print(f"✅ Serveur OK ! {data['cartes_loaded']} cartes disponibles\n")
        else:
            print("⚠️ Serveur répond mais erreur")
    except:
        print("❌ Serveur inaccessible - Vérifiez que api_server.py tourne\n")
    
    # Recherche de carte
    t_total_start = time.time()
    
    carte_trouvée = trouver_carte_via_api("templates/locklass.png")
    
    if carte_trouvée:
        print("\n" + "="*60)
        print("✅ RÉSULTAT")
        print("="*60)
        print(f"📋 Carte: {carte_trouvée['carte']}")
        print(f"🎯 Score: {carte_trouvée['score']}")
        print(f"⚡ Temps: {carte_trouvée['temps']}s")
        print("="*60)
        
        # Ouvrir Cardmarket
        print("\n🌐 Ouverture de Cardmarket...")
        ouvrir_cardmarket_precis(
            carte_trouvée["carte_infos"]["nom"],
            carte_trouvée["carte_infos"]["numero"]
        )
    else:
        print("\n❌ Échec de la recherche")
    
    t_total_end = time.time()
    print(f"\n⏰ TEMPS TOTAL: {t_total_end - t_total_start:.2f}s")
