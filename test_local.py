import json
import os
import webbrowser  # Ajout de l'importation


file_path_card = 'pokemon_db_light.json'
nom_poke = 'zekrom ex'
numero_poke = "172"
date = "2025"

# URL vers laquelle vous souhaitez rediriger
url_to_redirect = "http://example.com"  # Remplacez par votre URL

# Ouvrir l'URL dans le navigateur par défaut
webbrowser.open(url_to_redirect)

with open(file_path_card, 'r', encoding='utf-8') as f:
    cards_data = json.load(f)
    for card in cards_data:
        if card.get("name").lower() == nom_poke.lower() and card.get("number") == numero_poke and card.get("release_date", "").startswith(date):
            print(card["id"])



#Adresse vers cardmarket : https://prices.pokemontcg.io/cardmarket/swsh9tg-TG05