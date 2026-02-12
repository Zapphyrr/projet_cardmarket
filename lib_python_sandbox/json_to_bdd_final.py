import json




def crea_bdd():
    with open('pokemon_db_light.json', 'r', encoding='utf-8') as f:
        pdb = json.load(f)
        
    with open ('pokemon_card_bdd.csv', 'a', encoding='utf-8') as f:
        for card in pdb:
            name = card.get("name", "").replace('"', '\\"')
            number = card.get("number", "")
            set_name = card.get("set_name", "Unknown Set").replace('"', '\\"')
            image = card.get("image", "")
            release_date = card.get("release_date", "")
            ip_set_card = card.get("ip_set_card", "")
            line = f'{name} ; {number} ; {set_name} ; {image} ; {release_date} ; {ip_set_card}\n'
            f.write(line)
            
            
def crea_bdd_first_line():
    with open ('pokemon_card_bdd.csv', 'w', encoding='utf-8') as f:
        f.write('name ; number ; set_name ; image ; release_date ; ip_set_card\n')
        
        
crea_bdd_first_line()
crea_bdd()