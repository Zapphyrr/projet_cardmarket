import pandas as pd
import cv2
import requests
import numpy as np
import pickle
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

orb = cv2.ORB_create(nfeatures=80)  # Augmenté à 80 pour meilleure précision


def url_to_image(url):
    """Télécharge une image depuis une URL et la convertit pour OpenCV"""
    try:
        # 1. On télécharge l'image brute
        # stream=True permet de ne pas tout charger d'un coup si l'image est énorme
        resp = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
                
        # 2. On transforme les octets en tableau NumPy
        image_array = np.asarray(bytearray(resp.content), dtype=np.uint8)
        
        # 3. On décode l'image pour OpenCV (0 = Noir et Blanc direct, idéal pour SIFT)
        img = cv2.imdecode(image_array, 0)
        
        return img
    except Exception as e:
        print(f"Erreur de téléchargement pour {url}: {e}")
        return None


def process_one_card(row_data):
    index, row = row_data
    image_path = row['image'].strip()
    print("image_path:", image_path)
    
    print("card_id:", image_path)
    image_path = url_to_image(image_path)
    if image_path is not None:
        keypoints, descriptors = orb.detectAndCompute(image_path, None)
        if descriptors is not None and len(keypoints) > 10:
            # On n'a même pas besoin de sauvegarder les Keypoints (kp) pour la BDD
            # On sauvegarde JUSTE les descripteurs (des) et l'ID.
            # "des" est en uint8 (8 bits) au lieu de float32 (32 bits) -> 4x plus léger !
            return {
                'id': f"{row['number']}-{row['name']}-{row['set_name']}",
                'descriptors': descriptors
            }

if __name__ == '__main__':
    db_file = 'bdd/pokemon_card_bdd.csv' 
    df = pd.read_csv(db_file, sep=';')
    df.columns = df.columns.str.strip()
    
    tasks = list(df.iterrows())
    print("Démarrage Indexation ORB (Rapide & Léger)...")
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(tqdm(executor.map(process_one_card, tasks), total=len(tasks)))
        

    valid_results = [r for r in results if r is not None]
    print(f"Terminé ! {len(valid_results)} cartes indexées.")
    
    # Sauvegarde
    with open("orb_db.pkl", 'wb') as f:
        pickle.dump(valid_results, f)
    
    print("Base de données 'orb_db.pkl' créée.")

