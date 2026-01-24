import requests
from bs4 import BeautifulSoup
from pokemontcgsdk import Card
from pokemontcgsdk import Set
from pokemontcgsdk import Type
from pokemontcgsdk import Supertype
from pokemontcgsdk import Subtype
from pokemontcgsdk import Rarity
from pokemontcgsdk import RestClient

RestClient.configure('12345678-1234-1234-1234-123456789ABC')


apiKey = 'API'
pokemonName = 'Seismitoad'
cardNumber = '105'
releaseDate = '2025'


def getPokemonID(pokemonName, cardNumber):
    card = Card.where(q=f"name:{pokemonName} number:{cardNumber}" )
    
    # Card.where retourne directement les données, pas une URL à requêter
    if card and len(card) > 0:
        resultat_brut = [c.to_dict() if hasattr(c, 'to_dict') else c.__dict__ for c in card]
    
    if resultat_brut and len(resultat_brut) > 0:
        for poke_card in resultat_brut:
            # Adapter pour fonctionner avec les objets retournés par l'API
            card_data = poke_card['set']['releaseDate'] if isinstance(poke_card, dict) else poke_card.set.releaseDate
            if releaseDate in str(card_data):
                card_output = poke_card if isinstance(poke_card, dict) else poke_card.to_dict()
                
                print("ID trouvé:", card_output['id'])
                print("Nom:", card_output['name'])
                print("average sell price:", card_output['cardmarket']['prices']['averageSellPrice'])
                print("trendPrice:", card_output['cardmarket']['prices']['trendPrice'])
                print("lowPrice:", card_output['cardmarket']['prices']['lowPrice'])
                return get_french_price(card_output['cardmarket']['url'])
    else:
        print("Aucune carte trouvée")
        return None
  
  
def get_french_price(card_url):
    # On ajoute les filtres FR directement à l'URL
    filtered_url = f"{card_url}?language=2"
    print("URL filtrée pour la France:", filtered_url)
    # Headers indispensables pour ne pas être bloqué immédiatement
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(filtered_url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        
        # On cherche la première ligne d'article (l'offre la moins chère filtrée)
        # Note : La classe CSS peut varier, il faut l'inspecter sur le site
        first_offer_price = soup.select_one(".article-row .price-container .color-primary")
        
        if first_offer_price:
            return first_offer_price.text.strip()
        else:
            return "Aucune offre FR trouvée"
    else:
        return f"Erreur de connexion : {response.status_code}"
print(getPokemonID(pokemonName,cardNumber))
