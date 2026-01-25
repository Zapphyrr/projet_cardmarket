import json
import os
from time import time
from urllib import response
import webbrowser  # Ajout de l'importation
from bs4 import BeautifulSoup
import requests

file_path_card = 'pokemon_db_light.json'
nom_poke = 'Landorus'
numero_poke = "131"
date = "2025"



def scraper_prix_cardmarket(url_cm):
    print(f"Scraping Cardmarket pour l'URL : {url_cm}")
    # Headers plus complets pour simuler un vrai navigateur (Chrome)
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
    response = requests.get(url_redirect)
    print(f"URL de destination : {response.url}")
    
    # Nettoyer l'URL en supprimant les paramètres UTM s'ils existent
    url_dest = response.url.split('?')[0]  # Garder uniquement la base de l'URL
    url_dest = url_dest + "?language=2"  # Ajouter le filtre langue française
    
    return url_dest


def ouverture_auto_url(url):
    print(f"Ouverture automatique de l'URL dans le navigateur : {url}")
    webbrowser.open(url)




with open(file_path_card, 'r', encoding='utf-8') as f:
    cards_data = json.load(f)
    for card in cards_data:
        if card.get("name").lower() == nom_poke.lower() and card.get("number") == numero_poke and card.get("release_date", "").startswith(date):
            print(card["id"])
            id_carte = card["id"]
            
            url_cardmarket = url_tcg_api_to_cardmarket_fr(id_carte)
            
            '''''
            prix_extrait = scraper_prix_cardmarket(url_cardmarket)
            print("--- Données extraites de Cardmarket ---")
            if isinstance(prix_extrait, dict):
                for cle, valeur in prix_extrait.items():
                    print(f"{cle} : {valeur}")
            else:
                print(prix_extrait)
            '''''
            ouverture_auto_url(url_cardmarket)
            break



#Adresse vers cardmarket : https://prices.pokemontcg.io/cardmarket/swsh9tg-TG05

#https://api.pokemontcg.io/v2/cards?q=name:Zekrom ex number:172&apiKey=5458b921-95ba-4f7c-90b9-ba78bf07a233

