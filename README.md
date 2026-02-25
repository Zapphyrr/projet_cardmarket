# PokeScan CardMarket

Application mobile Flutter pour scanner une carte du TCG Pokémon, l'identifier via une API de vision par ordinateur, puis ouvrir automatiquement la page Cardmarket correspondante (marché FR).

## Petite Demo de l'API

- Health check: https://projectcardmarket-production.up.railway.app//health

## Fonctionnalites

- Scan de carte avec detection des 4 coins et recadrage automatique
- Envoi direct de l'image recadree a l'API IA
- Reconnaissance de carte par ORB + FLANN (OpenCV)
- Redirection automatique vers Cardmarket en navigateur externe
- Filtrage langue FR (`language=2`) pour les prix Cardmarket (/!\ ne fonctionne pas encore /!\)

## Stack technique

### Mobile
- Flutter (Dart)
- `cunning_document_scanner`
- `http`
- `url_launcher`

### Backend IA
- Python 3.11
- Flask + Flask-CORS
- OpenCV (`opencv-python-headless`), NumPy, Pillow
- Gunicorn
- Deploiement Railway

## Architecture

- `flutter_application_1/`: application mobile
- `lib_python_sandbox/`: API Flask de reconnaissance
- `pokemon-tcg-data-master/`: source des donnees cartes Pokemon
- `json_to_bd.py`: generation base de donnees legere
- `railway.toml`: config de deploiement Railway

## Lancer le projet

### 1) App Flutter

```bash
cd flutter_application_1
flutter pub get
flutter run
```

### 2) API locale (optionnel)

```bash
cd lib_python_sandbox
pip install -r requirements.txt
python api_server.py
```

## Endpoints API

- `GET /health` -> statut service + nombre de cartes chargees
- `POST /search` -> recoit une image (base64) et retourne la carte la plus probable

## Notes

- Cardmarket bloque souvent les clients HTTP classiques (403), la redirection finale est ouverte dans le navigateur externe.
- /!\ L'application n'est pas affiliee a Cardmarket /!\.

## Auteur

- GitHub: https://github.com/Zapphyrr
