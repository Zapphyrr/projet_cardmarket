import json
import cloudscraper
import os
from time import time
from urllib import response
import webbrowser  # Ajout de l'importation
from bs4 import BeautifulSoup
import requests
import urllib.parse
import difflib

file_path_card = 'pokemon_db_light.json'
nom_poke = 'mega-dracaufeu'
numero_poke = "151"
date = "2025"
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
scraper = cloudscraper.create_scraper()


def scraper_prix_cardmarket(url_cm):
    print(f"Scraping Cardmarket pour l'URL : {url_cm}")
    # Headers plus complets pour simuler un vrai navigateur (Chrome)


    try:
        # Utiliser une session permet de simuler un comportement plus humain
        session = requests.Session()
        
        # On fait une petite pause avant de charger pour ne pas paraître trop rapide
        
        
        response = session.get(url_cm, headers=headers, timeout=15)

        if response.status_code == 403:
            return "Accès toujours bloqué (403). Cardmarket protège ses données."

        # 2. On scrape la page de destination
        soup = BeautifulSoup(response.text, 'html.parser')
        resultats = {}

        # On utilise structure <dt> et <dd> de l'html pour extraire les données
        for dt, dd in zip(soup.find_all('dt'), soup.find_all('dd')):
            label = dt.get_text(strip=True)
            span = dd.find('span')
            valeur = span.get_text(strip=True) if span else dd.get_text(strip=True)
            resultats[label] = valeur
        
        return resultats

    except Exception as e:
        return f"Erreur : {e}"


def url_tcg_api_to_cardmarket_fr(card_id):
    url_redirect = str(f"https://prices.pokemontcg.io/cardmarket/{card_id}")
    # 1. redirection pour avoir la vraie page Cardmarket
    session = requests.Session()
    response = session.get(url_redirect, headers=headers, timeout=15)
    print(f"URL de destination : {response.url}")
    
    # Nettoyer l'URL en supprimant les paramètres UTM s'ils existent
    url_dest = response.url.split('?')[0]  # Garder uniquement la base de l'URL
    url_dest = url_dest + "?language=2"  # Ajouter le filtre langue française
    
    return url_dest


def ouverture_auto_url(url):
    print(f"Ouverture automatique de l'URL dans le navigateur : {url}")
    webbrowser.open(url)

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
        
    
    
    
    
ouvrir_cardmarket_precis("MEG", numero_poke)   
def trouver_et_ouvrir_la_bonne_carte(nom_poke, numero, nom_extension_bdd):
    print(f"🔍 Recherche de : {nom_poke} {numero} (Extension voulue : {nom_extension_bdd})")

    # 1. On cherche large : Nom + Numéro
    query = f"{nom_poke} {numero}"
    url_recherche = f"https://www.cardmarket.com/fr/Pokemon/Products/Search?searchString={urllib.parse.quote(query)}"
    
    try:
        response = scraper.get(url_recherche)
        
        # Cas A : Redirection directe (Cardmarket a trouvé une seule carte unique)
        if "/Products/Cards/" in response.url:
            print("✅ Carte unique trouvée directement !")
            webbrowser.open(response.url + "?language=2") # Ouvre en FR
            return

        # Cas B : Liste de résultats (C'est là que ton problème arrive)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select(".table-body .row")

        if not rows:
            print("❌ Aucune carte trouvée.")
            return

        print(f"⚠️ {len(rows)} résultats trouvés. Filtrage en cours...")
        
        meilleur_lien = None
        
        for row in rows:
            # Extraction des infos de la ligne
            lien_element = row.select_one(".col-12.col-md-4 a")
            extension_element = row.select_one(".col-icon.d-none.d-md-block a") # L'icône/nom de l'extension
            
            if not lien_element or not extension_element:
                continue

            nom_extension_cm = extension_element['title'].strip() # Ex: "Stars Étincelantes" ou "Star Birth"
            lien_partiel = lien_element['href']
            
            # --- LE FILTRE MAGIQUE ---
            # On compare le nom de l'extension de ta BDD avec celui de Cardmarket
            # On utilise difflib pour gérer les petites différences (ex: "&" vs "and")
            ratio = difflib.SequenceMatcher(None, nom_extension_bdd.lower(), nom_extension_cm.lower()).ratio()
            
            print(f"   -> Trouvé : {nom_extension_cm} (Correspondance : {int(ratio*100)}%)")

            # Si ça correspond à plus de 80% (ou si c'est exactement le même)
            if ratio > 0.8: 
                meilleur_lien = "https://www.cardmarket.com" + lien_partiel
                break # On a trouvé, on arrête de chercher !

        # 3. Résultat final
        if meilleur_lien:
            print(f"🚀 Victoire ! Ouverture de : {meilleur_lien}")
            # On ajoute language=1 (Anglais) ou 2 (Français) pour forcer le filtre sur la page
            webbrowser.open(meilleur_lien + "?language=1") 
        else:
            print("❌ Impossible de distinguer la bonne version. Ouverture de la recherche globale.")
            webbrowser.open(url_recherche)

    except Exception as e:
        print(f"Erreur : {e}")

"""
ouvrir_cardmarket_precis(nom_poke, numero_poke)
with open(file_path_card, 'r', encoding='utf-8') as f:
    cards_data = json.load(f)
    for card in cards_data:
        db_name = card.get("name", "").lower().strip()
        search_name = nom_poke.lower().replace("-", " ").strip()
        
        if search_name in db_name and card.get("number") == numero_poke and card.get("release_date", "").startswith(date):
            print(search_name)
            print(card["id"])
            print("set : ",card.get("set_name", ""))
            id_carte = card["id"]
            nom_set = card.get("set_name", "")
            #ouvrir_cardmarket_precis(nom_poke, numero_poke, nom_set)
            #trouver_et_ouvrir_la_bonne_carte(nom_poke, numero_poke, card.get("set_name", ""))
            
            
            
            #url_cardmarket = url_tcg_api_to_cardmarket_fr(id_carte)
"""
        
"""
            prix_extrait = scraper_prix_cardmarket(url_cardmarket)
            print("--- Données extraites de Cardmarket ---")
            if isinstance(prix_extrait, dict):
                for cle, valeur in prix_extrait.items():
                    print(f"{cle} : {valeur}")
            else:
                print(prix_extrait)
            
            #ouverture_auto_url(url_cardmarket)
            break

"""

#Adresse vers cardmarket : https://prices.pokemontcg.io/cardmarket/swsh9tg-TG05

#https://api.pokemontcg.io/v2/cards?q=name:Zekrom ex number:172&apiKey=5458b921-95ba-4f7c-90b9-ba78bf07a233

