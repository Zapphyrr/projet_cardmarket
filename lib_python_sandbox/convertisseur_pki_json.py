import pickle
import json
import numpy as np

# Fonction pour convertir les tableaux numpy en listes (pour le JSON)
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

print("🔄 Conversion du PKL vers JSON pour Flutter...")

with open("orb_db.pkl", 'rb') as f:
    db_data = pickle.load(f)

# On nettoie les données pour ne garder que l'essentiel
json_db = []
for carte in db_data:
    if carte['descriptors'] is not None:
        json_db.append({
            'id': carte['id'], # Format "Set-Numero"
            # On stocke les descripteurs sous forme de liste simple
            'descriptors': carte['descriptors'] 
        })

with open("flutter_db.json", "w") as f:
    json.dump(json_db, f, cls=NumpyEncoder)

print("✅ Fichier 'flutter_db.json' généré ! Copie-le dans ton projet Flutter.")