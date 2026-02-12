import pandas as pd
import cv2
import requests
import numpy as np
import pickle  # Pour sauvegarder le résultat final
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm # Barre de progression


sift = cv2.SIFT_create()


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

def pack_keypoint(keypoint):
    return (keypoint.pt, keypoint.size, keypoint.angle, keypoint.response, keypoint.octave, keypoint.class_id)

def process_one_card(row_data):
    index, row = row_data
    image_path = row['image'].strip()
    print("image_path:", image_path)
    
    print("card_id:", image_path)
    image_path = url_to_image(image_path)
    if image_path is not None:
        keypoints, descriptors = sift.detectAndCompute(image_path, None)
        if descriptors is not None:
            keypoints_list = [pack_keypoint(kp) for kp in keypoints]
            return {
                'name': row['name'],
                'number': row['number'],
                'set_name': row['set_name'],
                'keypoints': keypoints_list,
                'descriptors': descriptors
            }
    else:
        print(f"Image non trouvée : {image_path}")
        return {"Erreur", image_path}
            
    print(f"Indexation terminée. {len(db_features)} images indexées.")
if __name__ == '__main__':
    db_features = []
    db_file = ' templates/pokemon_card_bdd.csv'
    df = pd.read_csv(db_file, sep=';')

    # Retirer les espaces des noms de colonnes
    df.columns = df.columns.str.strip()

    print("Colonnes du DataFrame :", df.columns.tolist())
    print(df.head())

    missing_values = df.isnull().sum().sum()
    print(f"Nombre total de valeurs manquantes dans la BDD : {missing_values}")


    tache = list(df.iterrows())

    print("Indexation des images et calcul des fingerprints")
    with ThreadPoolExecutor(max_workers=50) as executor:
        # tqdm affiche la barre de progression
        results = list(tqdm(executor.map(process_one_card, tache), total=len(tache)))
        
    for res in results:
        if res is not None:
            if "Erreur" not in res:
                db_features.append(res)
            else :
                print("Problème avec l'image :", res)
        

    print(f"Indexation terminée ! {len(db_features)} cartes valides sur {len(df)}.")

    # SAUVEGARDE SUR LE DISQUE
    output_filename = "features_db.pkl"
    print(f"Sauvegarde des données dans {output_filename}...")
    with open(output_filename, 'wb') as f:
        pickle.dump(db_features, f)
        
    print("Sauvegarde terminée ! Check ton fichier.", output_filename)




















def trouver_cartes(photo_user_path):
    keypoints_user, descriptors_user = sift.detectAndCompute(photo_user_path, None)
    if descriptors_user is None:
        print("Aucun descripteur trouvé pour l'image utilisateur.")
        return []
    
    matches_list = []
    
    
    # Trier par nombre de bons matches décroissant
    matches_list.sort(key=lambda x: x[1], reverse=True)
    
    # Retourner les top 5 correspondances
    top_matches = matches_list[:5]
    result_cards = []
    for match in top_matches:
        index = match[0]
        result_cards.append({
            'name': df.at[index, 'name'],
            'number': df.at[index, 'number'],
            'set_name': df.at[index, 'set_name'],
            'image': df.at[index, 'image'],
            'good_matches': match[1]
        })
    
    return result_cards