import cv2
import pickle
import numpy as np
import time
import requests
import urllib.parse
import webbrowser

# ========== CHRONOMÈTRE DÉBUT ==========
temps_debut_total = time.time()
print("🕐 Démarrage du programme...")

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
t_load_start = time.time()
print("Chargement BDD ORB...")
with open("orb_db.pkl", 'rb') as f:
    DB_CARTES = pickle.load(f)
t_load_end = time.time()
print(f"✅ {len(DB_CARTES)} cartes chargées en {t_load_end - t_load_start:.2f}s")

# Initialisation de l'ia ORB
orb = cv2.ORB_create(nfeatures=150) # ALIGNÉ avec la base : 150 features

# --- CONFIGURATION FLANN LSH AGRESSIVE ---
print("Préparation du matcher FLANN agressif...")
t_matcher_start = time.time()

FLANN_INDEX_LSH = 6
index_params = dict(
    algorithm=FLANN_INDEX_LSH,
    table_number=2,      # AGRESSIF : 2 tables minimum
    key_size=8,
    multi_probe_level=1
)
search_params = dict(checks=1)  # AGRESSIF : 1 check seulement

matcher = cv2.FlannBasedMatcher(index_params, search_params)

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

# Entraînement FLANN
matcher.add([super_matrix])
matcher.train()

t_matcher_end = time.time()
print(f"✅ FLANN optimisé prêt en {t_matcher_end - t_matcher_start:.2f}s!")

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

    # OPTIMISATION 1: Réduire la taille de l'image AGRESSIVE
    max_dimension = 300  # AGRESSIF : 300px pour vitesse max
    height, width = img.shape
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        print(f"Image redimensionnée: {width}x{height} → {new_width}x{new_height}")

    t_orb_start = time.time()
    # Calcul ORB user
    kp_user, des_user = orb.detectAndCompute(img, None)
    if des_user is None: return "Pas de détails détectés"
    t_orb_end = time.time()
    print(f"⏱️  ORB extraction: {t_orb_end - t_orb_start:.2f}s")
    print(f"Descripteurs extraits: {len(des_user)}")

    t_match_start = time.time()
    # RECHERCHE FLANN ultra-optimisé
    matches = matcher.knnMatch(des_user, k=2)
    t_match_end = time.time()
    print(f"⏱️  FLANN knnMatch: {t_match_end - t_match_start:.2f}s")
    print(f"Matches trouvés: {len(matches)}")
    
    t_filter_start = time.time()
    # Filtrage (Ratio test) - MOINS STRICT pour avoir plus de matches
    good_matches = []
    for match_pair in matches:
        if len(match_pair) < 2: continue
        m, n = match_pair
        if m.distance < 0.75 * n.distance:  # Moins strict (0.75) pour plus de résultats
            good_matches.append(m)
    t_filter_end = time.time()
    print(f"⏱️  Filtrage: {t_filter_end - t_filter_start:.2f}s")
    print(f"Good matches après filtrage: {len(good_matches)}")
    
    t_vote_start = time.time()
    # COMPTER LES VOTES
    votes = {}
    for match in good_matches:
        idx_in_super_matrix = match.trainIdx
        card_id = map_descriptor_to_card_id[idx_in_super_matrix]
        votes[card_id] = votes.get(card_id, 0) + 1
    
    # Trouver le gagnant
    if not votes:
        return "Aucune correspondance."

    meilleur_id = max(votes, key=votes.get)
    score = votes[meilleur_id]
    t_vote_end = time.time()
    print(f"⏱️  Vote: {t_vote_end - t_vote_start:.2f}s")
    
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
print("\n" + "="*50)
print("🔍 DÉBUT DE LA RECHERCHE")
print("="*50)
t_recherche_start = time.time()

carte_trouvé = trouver_carte_rapide("templates/zeblitz.png")

t_recherche_end = time.time()
print(f"\n⏱️  Temps recherche: {t_recherche_end - t_recherche_start:.2f}s")

# Vérifier si la recherche a réussi
if isinstance(carte_trouvé, dict):
    print(f"📋 Carte trouvée: {carte_trouvé['carte']}")
    print(f"🎯 Score: {carte_trouvé['score']}")
    print(f"⚡ Temps interne fonction: {carte_trouvé['temps']}s")
    
    t_cardmarket_start = time.time()
    ouvrir_cardmarket_precis(carte_trouvé["carte_infos"]["nom"], carte_trouvé["carte_infos"]["numero"])
    t_cardmarket_end = time.time()
    print(f"🌐 Ouverture Cardmarket: {t_cardmarket_end - t_cardmarket_start:.2f}s")
else:
    print(f"❌ ÉCHEC: {carte_trouvé}")
    print("💡 Essayez d'augmenter les features ou d'ajuster le ratio test")

# ========== CHRONOMÈTRE FIN ==========
temps_fin_total = time.time()
temps_total = temps_fin_total - temps_debut_total
print("\n" + "="*50)
print(f"⏰ TEMPS TOTAL DU PROGRAMME: {temps_total:.2f}s")
print("="*50)