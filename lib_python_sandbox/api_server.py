from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import pickle
import numpy as np
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app)  # Permettre requêtes depuis Flutter

# ========== CHARGEMENT DE LA BASE (Au démarrage du serveur) ==========
print("🔄 Chargement de la base de données...")
with open("orb_db.pkl", 'rb') as f:
    DB_CARTES = pickle.load(f)
print(f"✅ {len(DB_CARTES)} cartes chargées")

# Configuration ORB et FLANN
orb = cv2.ORB_create(nfeatures=150)

FLANN_INDEX_LSH = 6
index_params = dict(
    algorithm=FLANN_INDEX_LSH,
    table_number=2,
    key_size=8,
    multi_probe_level=1
)
search_params = dict(checks=1)
matcher = cv2.FlannBasedMatcher(index_params, search_params)

# Construction super_matrix
all_descriptors = []
map_descriptor_to_card_id = []

for carte in DB_CARTES:
    desc = carte['descriptors']
    if desc is not None:
        all_descriptors.append(desc)
        map_descriptor_to_card_id.extend([carte['id']] * len(desc))

super_matrix = np.vstack(all_descriptors)
matcher.add([super_matrix])
matcher.train()
print("✅ Matcher FLANN prêt !")

def extraire_infos_carte(card_id):
    """Extrait nom, numéro, set depuis l'ID"""
    if not isinstance(card_id, str):
        return {"numero": "", "nom": "", "set_name": "", "carte_texte": str(card_id)}
    
    parts = card_id.split("-")
    if len(parts) < 3:
        numero = parts[0].strip() if parts else ""
        nom = "-".join(parts[1:]).strip() if len(parts) > 1 else ""
        set_name = ""
    else:
        numero = parts[0].strip()
        set_name = parts[-1].strip()
        nom = "-".join(parts[1:-1]).strip()
    
    carte_texte = f"{numero} - {nom} - {set_name}".strip()
    return {"numero": numero, "nom": nom, "set_name": set_name, "carte_texte": carte_texte}

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé pour vérifier que le serveur tourne"""
    return jsonify({"status": "ok", "cartes_loaded": len(DB_CARTES)})

@app.route('/search', methods=['POST'])
def search_card():
    """Endpoint principal : reçoit image en base64, retourne carte trouvée"""
    try:
        # Récupérer l'image base64 depuis la requête
        data = request.get_json()
        image_base64 = data.get('image')
        
        if not image_base64:
            return jsonify({"error": "Image manquante"}), 400
        
        # Décoder l'image base64
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes)).convert('L')  # Convertir en grayscale
        img_array = np.array(image)
        
        # Redimensionner si trop grande
        max_dimension = 300
        height, width = img_array.shape
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img_array = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Extraction ORB
        kp_user, des_user = orb.detectAndCompute(img_array, None)
        if des_user is None:
            return jsonify({"error": "Aucun détail détecté dans l'image"}), 400
        
        # Recherche FLANN
        matches = matcher.knnMatch(des_user, k=2)
        
        # Filtrage ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) < 2:
                continue
            m, n = match_pair
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        
        # Comptage votes
        votes = {}
        for match in good_matches:
            idx_in_super_matrix = match.trainIdx
            card_id = map_descriptor_to_card_id[idx_in_super_matrix]
            votes[card_id] = votes.get(card_id, 0) + 1
        
        if not votes:
            return jsonify({"error": "Aucune correspondance trouvée"}), 404
        
        # Meilleur match
        meilleur_id = max(votes, key=votes.get)
        score = votes[meilleur_id]
        infos = extraire_infos_carte(meilleur_id)
        
        # Retour JSON
        return jsonify({
            "success": True,
            "carte": infos["carte_texte"],
            "numero": infos["numero"],
            "nom": infos["nom"],
            "set_name": infos["set_name"],
            "score": score,
            "matches_count": len(good_matches)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # En production, utilisez gunicorn au lieu de app.run()
    app.run(host='0.0.0.0', port=5000, debug=False)
