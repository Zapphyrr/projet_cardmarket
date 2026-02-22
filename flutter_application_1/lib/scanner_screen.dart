import 'dart:io';
import 'package:flutter/material.dart';
import 'package:cunning_document_scanner/cunning_document_scanner.dart';
import 'tools.dart' as tool;
import 'api_service.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  File? _imagePrise;
  bool _isScanning = false;
  String _resultatScan = "Appuyez sur le bouton pour scanner une carte";
  int? _scoreIA; // Score de confiance de l'IA


  // Scanner une carte : recadrage automatique + analyse IA
  Future<void> scannerCarte() async {
    try {
      setState(() {
        _isScanning = true;
        _resultatScan = "📸 Scanning de la carte...";
      });

      // cunning_document_scanner va automatiquement :
      // 1. Ouvrir la caméra avec détection en temps réel des bords
      // 2. Détecter les 4 coins de la carte Pokemon
      // 3. Corriger la perspective si la carte est inclinée/penchée
      // 4. Recadrer pour garder uniquement la carte (élimine table, doigts, etc.)
      // 5. Retourner l'image recadrée et nettoyée
      // 
      // AVANTAGE : Réduit la taille de l'image de ~3MB à ~500KB
      // et élimine 80% du bruit pour l'API IA !
      
      List<String>? pictures = await CunningDocumentScanner.getPictures(
        noOfPages: 1, // Une seule carte à scanner
        isGalleryImportAllowed: false, // Forcer l'utilisation de la caméra
        // Note: cunning_document_scanner v1.0.4 ne permet pas de désactiver
        // le délai de stabilisation natif (3-5s). Pour une capture instantanée,
        // il faudrait modifier le code natif Android/iOS ou utiliser image_picker
        // avec edge_detection en remplacement.
      );

      if (pictures != null && pictures.isNotEmpty) {
        setState(() {
          _imagePrise = File(pictures.first);
          _resultatScan = "Analyse IA en cours...\nCela peut prendre 5-10 secondes.";
        });
        
        // Lancer automatiquement l'analyse IA
        await scannerAvecIA();
      } else {
        setState(() {
          _isScanning = false;
          _resultatScan = "KO : Scan annulé";
        });
      }
    } catch (e) {
      setState(() {
        _isScanning = false;
        _resultatScan = "KO : Erreur scan : $e\n\n Vérifiez les permissions caméra.";
      });
    }
  }

  // 4) Scanner avec IA (API Railway)
  Future<void> scannerAvecIA() async {
    if (_imagePrise == null) {
      setState(() {
        _resultatScan = "KO : Prenez d'abord une photo !";
      });
      return;
    }

    // L'état est déjà géré par scannerCarte()
    if (!_isScanning) {
      setState(() {
        _isScanning = true;
        _resultatScan = "Analyse IA en cours...\nCela peut prendre 5-10 secondes.";
      });
    }

    try {
      final result = await CardRecognitionAPI.searchCard(_imagePrise!);

      if (result != null && result['success'] == true) {
        final String nomCarte = result['nom'] ?? '';
        final String numero = result['numero'] ?? '';
        final String set = result['set_name'] ?? '';
        final int score = result['score'] ?? 0;

        setState(() {
          _isScanning = false;
          _scoreIA = score;
          _resultatScan = "OK : Carte trouvée !\n$nomCarte\n$numero - $set\n🎯 Score: $score";
        });

        // Ouvrir Cardmarket automatiquement
        tool.ouvrirCardmarketPrecis(nomCarte, numero);
      } else {
        setState(() {
          _isScanning = false;
          _resultatScan = "KO ${result?['error'] ?? 'Carte non trouvée'}\n\n💡 Conseil: Essayez avec un meilleur éclairage.";
        });
      }
    } catch (e) {
      setState(() {
        _isScanning = false;
        _resultatScan = "KO : Erreur: $e";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scanner de Carte')),
      body: Column(
        children: [
          Container(
            height: 350,
            width: double.infinity,
            child: _imagePrise != null
                ? Image.file(
                    _imagePrise!,
                    fit: BoxFit.contain,
                  )
                : Container(
                    color: Colors.grey[200],
                    child: const Center(
                      child: Icon(Icons.camera_alt, size: 50, color: Colors.grey),
                    ),
                  ),
          ),
          Container(
            height: 80,
            padding: const EdgeInsets.all(10),
            child: Center(
              child: _isScanning
                  ? const CircularProgressIndicator()
                  : Text(
                      _resultatScan,
                      style: const TextStyle(fontSize: 14),
                      textAlign: TextAlign.center,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                    ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20.0),
            child: Column(
              children: [
                // Bouton unique : Scanner avec IA
                ElevatedButton.icon(
                  onPressed: _isScanning ? null : scannerCarte,
                  icon: const Icon(Icons.document_scanner),
                  label: const Text('Scanner une carte Pokemon'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 55),
                    backgroundColor: Colors.deepPurple,
                    foregroundColor: Colors.white,
                    textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(height: 30),
              ],
            ),
          ),
        ],
      ),
    );
  }
}