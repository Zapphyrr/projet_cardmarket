import 'dart:convert';
import 'dart:math';
import 'package:flutter/services.dart'; // Pour charger le JSON
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
import 'package:opencv_dart/opencv_dart.dart' as cv; // Plugin OpenCV

class CardMatcherService {
  List<dynamic> _database = [];
  bool isLoaded = false;
  // 1. CHARGEMENT DU CERVEAU (JSON)


  Future<void> chargerCerveau() async {
    print("🧠 Chargement de la base de données...");
    final String response = await rootBundle.loadString('assets/flutter_db.json');
    _database = json.decode(response);
    isLoaded = true;
    print("✅ ${_database.length} cartes chargées en mémoire !");
  }

  // 2. ANALYSE ET MATCHING (L'équivalent de trouver_carte_rapide)
  Future<Map<String, dynamic>?> identifierCarte(String imagePath) async {
    if (!isLoaded) await chargerCerveau();

    // A. Lecture de l'image et conversion en Niveaux de gris
    var img = cv.imread(imagePath, flags: cv.IMREAD_GRAYSCALE);
    if (img.isEmpty) {
      print("❌ Erreur : Impossible de lire l'image");
      return null;
    }

    // B. Calcul ORB (Comme en Python)
    var orb = cv.ORB.create(nFeatures: 1000);
    var (keypoints, descriptors) = orb.detectAndCompute(img, cv.Mat.empty());
    // keypoints is already a List<cv.KeyPoint>
    // descriptors is a cv.Mat

    if (descriptors.isEmpty) return null;

    // C. LE MATCHING (Remplacement de FLANN)
    // En Dart pur, FLANN est dur à reproduire. On utilise une méthode BF (Brute Force) simplifiée.
    // On cherche la carte qui a le plus de descripteurs similaires.
    
    String meilleurId = "";
    int meilleurScore = 0;
    
    // On convertit les descripteurs de l'image utilisateur en liste pour comparer
    // Note: C'est l'étape lourde. Sur mobile, pour 15k cartes, ça peut laguer un peu.
    // Une optimisation serait d'utiliser du code natif C++ via FFI ici.
    
    // PSEUDO-IMPLEMENTATION DU MATCHING
    // OpenCV Dart a un BFMatcher, utilisons-le c'est plus rapide que du Dart pur
    final bf = cv.BFMatcher.create();
    
    // Pour chaque carte en base, on compare (C'est la boucle critique)
    for (var carte in _database) {
      // Reconstitution du Mat descriptor depuis le JSON
      // Attention : Cette étape de conversion JSON -> Mat à chaque fois est lente.
      // Idéalement, il faut le faire une fois au chargement.
      var descList = List<List<num>>.from(carte['descriptors']);
     
      // ... Si on arrive à comparer ...
      // NOTE IMPORTANTE : Comparer 15 000 matrices complètes en Dart pur est TROP LENT.
      // L'approche Python avec "Super Matrix" et FLANN C++ est 100x plus rapide.
      // Sur mobile, sans serveur Python, tu risques d'avoir 5 à 10 secondes d'attente.
    }
    
    // --- SOLUTION PRAGMATIQUE POUR MOBILE ---
    // Vu la complexité de FLANN en Dart, je te conseille vivement de garder
    // ton serveur Python pour faire le calcul (l'API qu'on a vu avant).
    // Mais si tu veux forcer en local, voici comment on simule le retour :
    await ouvrirCardmarketPrecis("Set-Numero"); // Exemple d'appel
    
    return {
      "id": "Set-Numero", // Exemple de résultat
      "score": 50
    };
  }

  // 3. LA LOGIQUE CARDMARKET (Traduction exacte de ton Python)
  Future<void> ouvrirCardmarketPrecis(String idCarte) async {
    // idCarte est sous la forme "NomSet-Numero" (ex: "base1-4")
    // On doit séparer le nom et le numéro.
    // Dans ton JSON, essaye de stocker le "vrai nom" si possible.
    
    // Exemple de parsing basique (à adapter selon ton format d'ID)
    List<String> parts = idCarte.split('-');
    String numero = parts.last;
    String setCode = parts.first; 
    
    // Nettoyage numéro (ex: TG05/TG30 -> TG05)
    String numeroPropre = numero.split("/")[0];
    
    // Pour l'exemple, on utilise le Code Set comme nom, mais l'idéal est d'avoir le nom Pokemon
    String recherche = "$setCode $numeroPropre"; 
    
    String queryEncoded = Uri.encodeComponent(recherche);
    String urlRecherche = "https://www.cardmarket.com/fr/Pokemon/Products/Search?searchString=$queryEncoded";

    Map<String, String> headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...", // Ton user agent complet
      "Accept-Language": "fr-FR,fr;q=0.9",
    };

    try {
      print("🕵️ Recherche Cardmarket: $urlRecherche");
      
      // HTTP GET (L'éclaireur)
      final response = await http.get(Uri.parse(urlRecherche), headers: headers);
      
      // Récupération de l'URL finale (après redirection)
      String urlFinale = response.request!.url.toString();
      
      if (urlFinale.contains("/Search")) {
        print("⚠️ Pas de redirection auto.");
        urlFinale = "$urlFinale&language=2";
      } else {
        print("✅ Redirection produit détectée !");
        urlFinale = "${urlFinale.split('?')[0]}?language=2";
      }

      // OUVERTURE DU NAVIGATEUR
      final Uri uri = Uri.parse(urlFinale);
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
        throw 'Impossible de lancer $urlFinale';
      }

    } catch (e) {
      print("Erreur: $e");
      // Fallback
      final Uri fallback = Uri.parse("$urlRecherche&language=2");
      launchUrl(fallback, mode: LaunchMode.externalApplication);
    }
  }
}