import requests
from bs4 import BeautifulSoup

apiKey = 'feef8208-7430-4ced-bab1-ed25a6ca64bb'
pokemonName = 'Zekrom'
cardNumber = '172'
releaseDate = '2025'


def getPokemonID(pokemonName, cardNumber):
    url = f"https://api.pokemontcg.io/v2/cards?q=name:{pokemonName} number:{cardNumber}" #?language=2
    headers = {'X-Api-Key': apiKey}
    
    output = requests.get(url, headers=headers)
    resultat_brut = output.json()
    
    if len(resultat_brut['data']) > 0:
        for poke_card in resultat_brut['data']:
            if releaseDate in poke_card['set']['releaseDate']:
                card = poke_card
                
                print("ID trouvé:", card['id'])
                print("Nom:", card['name'])
                print("average sell price:", card['cardmarket']['prices']['averageSellPrice'])
                print("trendPrice:", card['cardmarket']['prices']['trendPrice'])
                print("lowPrice:", card['cardmarket']['prices']['lowPrice'])
                return get_french_price(card['cardmarket']['url'])
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
