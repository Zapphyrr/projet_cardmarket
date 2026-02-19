import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class CardRecognitionAPI {
  // URL Railway déployée
  static const String API_URL = "https://projetcardmarket-production.up.railway.app/";
  
  /// Envoie une image au serveur et retourne les infos de la carte
  static Future<Map<String, dynamic>?> searchCard(File imageFile) async {
    try {
      // 1. Lire l'image et la convertir en base64
      final bytes = await imageFile.readAsBytes();
      final base64Image = base64Encode(bytes);
      
      // 2. Envoyer la requête POST
      final response = await http.post(
        Uri.parse('$API_URL/search'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'image': base64Image,
        }),
      ).timeout(const Duration(seconds: 60)); // Timeout 60s (IA peut être lente)
      
      // 3. Traiter la réponse
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          'success': true,
          'carte': data['carte'],
          'numero': data['numero'],
          'nom': data['nom'],
          'set_name': data['set_name'],
          'score': data['score'],
        };
      } else if (response.statusCode == 404) {
        return {
          'success': false,
          'error': 'Carte non trouvée',
        };
      } else {
        return {
          'success': false,
          'error': 'Erreur serveur: ${response.statusCode}',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'error': 'Erreur réseau: $e',
      };
    }
  }
  
  /// Vérifie que le serveur est accessible
  static Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$API_URL/health'),
      ).timeout(const Duration(seconds: 5));
      
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
