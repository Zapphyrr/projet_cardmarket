import 'package:http/http.dart' as http; // Import nécessaire
import 'package:url_launcher/url_launcher.dart';
Future<String?> urlTcgApiToCardmarketFr(String cardId) async {
  // L'URL de redirection initiale
  final Uri urlRedirect = Uri.parse("https://prices.pokemontcg.io/cardmarket/$cardId");
  print("test");
  try {
    // 1. On fait la requête. Par défaut, le client http de Dart SUIT les redirections.
    final response = await http.get(urlRedirect);

    if (response.statusCode == 200) {
      // response.request!.url contient l'URL finale après redirection
      String finalUrl = response.request!.url.toString();
      
      print("URL de destination brute : $finalUrl");

      // 2. Nettoyage (split sur le '?') comme dans ton python
      finalUrl = finalUrl.split('?')[0];

      // 3. Ajout du filtre langue française
      finalUrl = "$finalUrl?language=2";

      return finalUrl;
    } else {
      print("Erreur lors de la requête : ${response.statusCode}");
      return null;
    }
  } catch (e) {
    print("Erreur réseau : $e");
    return null;
  }
}

// J'ai changé le type de retour en "Future<void>" car la fonction fait l'action elle-même
Future<String?> ouvrirCardmarketPrecis(String nom, String numero) async {
  // --- 1. NETTOYAGE ---
  String nomPropre = nom.toLowerCase().replaceAll("-", " ").trim();
  String numeroPropre = numero.split("/")[0];

  // --- 2. CONSTRUCTION DE LA REQUÊTE ---
  String recherche = "$nomPropre $numeroPropre";
  print("Recherche Cardmarket pour : '$recherche'");
  
  String queryEncoded = Uri.encodeComponent(recherche);
  String urlRecherche = "https://www.cardmarket.com/fr/Pokemon/Products/Search?searchString=$queryEncoded";

  Map<String, String> headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
  };

  String urlFinaleAOuvrir = "";

  try {
    // --- 3. REQUÊTE HTTP (L'éclaireur) ---
    final response = await http.get(Uri.parse(urlRecherche), headers: headers);
    String urlAtterrie = response.request!.url.toString();
    
    print("URL atterrie : $urlAtterrie");

    // --- 4. ANALYSE DU RÉSULTAT ---
    
    // CAS 1 : Pas de redirection auto
    if (urlAtterrie.contains("/Search")) {
      print("⚠️ Pas de redirection auto.");
      urlFinaleAOuvrir = "$urlAtterrie&language=2";
    } 
    // CAS 2 : Redirection réussie vers un produit
    else {
      print("✅ Redirection produit détectée !");
      urlFinaleAOuvrir = "${urlAtterrie.split('?')[0]}?language=2";
    }

  } catch (e) {
    print("Erreur ou Blocage : $e");
    // EN CAS D'ERREUR (Fallback)
    urlFinaleAOuvrir = "$urlRecherche&language=2";
  }

  // --- 5. ACTION : OUVERTURE DU NAVIGATEUR ---
  if (urlFinaleAOuvrir.isNotEmpty) {
    final Uri uri = Uri.parse(urlFinaleAOuvrir);
    
    // mode: LaunchMode.externalApplication -> Force l'ouverture dans Chrome/Safari (pas dans l'app)
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      print("Impossible de lancer $urlFinaleAOuvrir");
    }
  }
}