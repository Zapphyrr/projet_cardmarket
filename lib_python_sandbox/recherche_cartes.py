import cv2
import pickle
import numpy as np
import time
import requests
import urllib.parse
import webbrowser

# Configuration des headers pour les requêtes HTTP
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}

#Chargement de la base de données des cartes pré-indexées
print("Chargement BDD ORB...")
with open("orb_db.pkl", 'rb') as f:
    DB_CARTES = pickle.load(f)
print(f"✅ {len(DB_CARTES)} cartes chargées.")

# Initialisation de l'ia ORB
orb = cv2.ORB_create(nfeatures=1000) # On peut en prendre un peu plus sur la photo user

# --- CONFIGURATION FLANN LSH (La magie de la vitesse) ---
# Ces paramètres sont optimisés pour les descripteurs binaires (ORB)
FLANN_INDEX_LSH = 6
index_params = dict(algorithm=FLANN_INDEX_LSH,
                    table_number=6,      # 12
                    key_size=12,         # 20
                    multi_probe_level=1) # 2
search_params = dict(checks=50)      # Nombre de vérifications (plus c'est bas, plus c'est vite)

# On prépare le matcher FLANN
flann = cv2.FlannBasedMatcher(index_params, search_params)

# --- ASTUCE DE PERFORMANCE ---
# Au lieu de boucler en Python (lent), on va créer une SUPER MATRICE
# contenant TOUS les descripteurs de TOUTES les cartes.
# C'est technique, mais ça permet à OpenCV de tout calculer en C++ d'un coup.

print("Préparation de l'index FLANN (quelques secondes)...")
# On empile tous les descripteurs dans une seule grosse matrice
all_descriptors = []
map_descriptor_to_card_id = [] # Pour retrouver quelle ligne appartient à quelle carte

for carte in DB_CARTES:
    desc = carte['descriptors']
    if desc is not None:
        all_descriptors.append(desc)
        # On note que ces N descripteurs appartiennent à cette carte ID
        map_descriptor_to_card_id.extend([carte['id']] * len(desc))

# Conversion en super matrice numpy
super_matrix = np.vstack(all_descriptors)

# On entraîne FLANN sur tout ça d'un coup
flann.add([super_matrix])
flann.train()
print("✅ Index FLANN prêt !")

def extraire_infos_carte(card_id):
    if not isinstance(card_id, str):
        return {
            "numero": "",
            "nom": "",
            "set_name": "",
            "carte_texte": str(card_id)
        }

    parts = card_id.split("-")
    if len(parts) < 3:
        numero = parts[0].strip() if parts else ""
        nom = "-".join(parts[1:]).strip() if len(parts) > 1 else ""
        set_name = ""
    else:
        numero = parts[0].strip()
        set_name = parts[-1].strip()
        nom = "-".join(parts[1:-1]).strip()

    carte_texte = f"{numero} -{nom} - {set_name}".strip()
    return {
        "numero": numero,
        "nom": nom,
        "set_name": set_name,
        "carte_texte": carte_texte
    }

def trouver_carte_rapide(chemin_photo):
    t_start = time.time()
    
    img = cv2.imread(chemin_photo, 0)
    if img is None: return "Erreur image"

    # Calcul ORB user
    kp_user, des_user = orb.detectAndCompute(img, None)
    if des_user is None: return "Pas de détails détectés"

    # RECHERCHE FLANN (KNN=2)
    # Ça va chercher les correspondances dans la super matrice
    matches = flann.knnMatch(des_user, k=2)

    # Filtrage (Ratio test)
    # Moins strict qu'avec SIFT, 0.75 ou 0.8 marche bien pour ORB
    good_matches = []
    for match_pair in matches:
        if len(match_pair) < 2: continue
        m, n = match_pair
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    # COMPTER LES VOTES
    # Chaque bon match "vote" pour une carte ID
    votes = {}
    for match in good_matches:
        # On regarde dans notre map à quelle carte appartient ce descripteur trouvé
        idx_in_super_matrix = match.trainIdx
        card_id = map_descriptor_to_card_id[idx_in_super_matrix]
        
        votes[card_id] = votes.get(card_id, 0) + 1

    # Trouver le gagnant
    if not votes:
        return "Aucune correspondance."

    meilleur_id = max(votes, key=votes.get)
    score = votes[meilleur_id]
    
    t_end = time.time()

    infos = extraire_infos_carte(meilleur_id)
    
    return {
        "carte": infos["carte_texte"],
        "carte_infos": {
            "numero": infos["numero"],
            "nom": infos["nom"],
            "set_name": infos["set_name"]
        },
        "score": score,
        "temps": round(t_end - t_start, 4)
    }


def ouvrir_cardmarket_precis(nom, numero):
    nom.lower().replace("-", " ").strip()
    # 1. Nettoyage du numéro (si tu as "TG05/TG30", on garde juste "TG05")
    numero_propre = numero.split("/")[0]
    
    # 2. Construction de la requête : "Nom + Numéro + Nom du Set"
    # C'est la combinaison unique qui différencie l'anglaise de la japonaise
    recherche = f"{nom} {numero}"
    
    # 3. Encodage propre pour l'URL (les espaces deviennent %20)
    query_encoded = urllib.parse.quote(recherche)
    
    # 4. URL finale de recherche
    # On ajoute &exact=true pour dire à Cardmarket d'être strict (optionnel mais conseillé)
    url_recherche = f"https://www.cardmarket.com/fr/Pokemon/Products/Search?searchString={query_encoded}"

    try:
        session = requests.Session()
        response = session.get(url_recherche, headers=headers, timeout=15)  # Vérifie que la requête a réussi
        url_finale = response.url
        
        if "/Search" in url_finale:
            print("⚠️ Pas de redirection automatique (Plusieurs résultats trouvés).")
            # On ajoute le filtre langue à l'URL de RECHERCHE (c'est un &)
            url_finale = url_finale + "&language=2"
        
        # CAS 2 : Cardmarket a redirigé vers le produit (On est sur /Products/Singles/...)
        else:
            print("✅ Redirection réussie vers la carte !")
            # On nettoie l'URL pour enlever les tracking bizarres s'il y en a
            url_propre = url_finale.split('?')[0]
            # On ajoute le filtre langue à l'URL PRODUIT (c'est un ?)
            url_finale = url_propre + "?language=2"
        webbrowser.open(url_finale)
        
    except requests.RequestException as e:
        print(f"Erreur lors de la requête : {e}")
        webbrowser.open(url_finale + "&language=2")

# TEST
carte_trouvé = trouver_carte_rapide("templates/locklass.png")
print(trouver_carte_rapide("templates/locklass.png"))
print(carte_trouvé["carte"])
print("type de cartes", type(carte_trouvé["carte"]))
ouvrir_cardmarket_precis(carte_trouvé["carte_infos"]["nom"], carte_trouvé["carte_infos"]["numero"])