import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';
import 'tools.dart' as tool;
import 'api_service.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  // Scanner OCR
  final TextRecognizer textRecognizer = TextRecognizer(script: TextRecognitionScript.latin);

  File? _imagePrise;
  bool _isScanning = false;
  String _resultatScan = "Aucune carte scannée";
  String _scanMode = ""; // "OCR" ou "IA"
  int? _scoreIA; // Score de confiance de l'IA

  // 1) Prendre une photo (sans lancer l'analyse)
  Future<void> prendrePhoto() async {
    final ImagePicker picker = ImagePicker();
    final XFile? photo = await picker.pickImage(source: ImageSource.camera);

    if (photo != null) {
      setState(() {
        _imagePrise = File(photo.path);
        _resultatScan = "Photo prise ! Choisissez une méthode de scan.";
        _scanMode = "";
        _scoreIA = null;
      });
    }
  }

  // 3) Scanner avec OCR (méthode actuelle, rapide)
  Future<void> scannerAvecOCR() async {
    if (_imagePrise == null) {
      setState(() {
        _resultatScan = "❌ Prenez d'abord une photo !";
      });
      return;
    }

    setState(() {
      _isScanning = true;
      _scanMode = "OCR";
      _resultatScan = "🔤 Analyse OCR en cours...";
    });

    await analyserTexte(_imagePrise!);
  }

  // 4) Scanner avec IA (API Railway)
  Future<void> scannerAvecIA() async {
    if (_imagePrise == null) {
      setState(() {
        _resultatScan = "❌ Prenez d'abord une photo !";
      });
      return;
    }

    setState(() {
      _isScanning = true;
      _scanMode = "IA";
      _resultatScan = "Analyse IA en cours...\nCela peut prendre 5-10 secondes.";
    });

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
          _resultatScan = "✅ Carte trouvwée !\n$nomCarte\n$numero - $set\n🎯 Score: $score";
        });

        // Ouvrir Cardmarket automatiquement
        tool.ouvrirCardmarketPrecis(nomCarte, numero);
      } else {
        setState(() {
          _isScanning = false;
          _resultatScan = "❌ ${result?['error'] ?? 'Carte non trouvée'}\n\n💡 Conseil: Prenez une photo plus nette.";
        });
      }
    } catch (e) {
      setState(() {
        _isScanning = false;
        _resultatScan = "❌ Erreur: $e";
      });
    }
  }

  // 5) Analyse OCR et extraction des infos
  Future<void> analyserTexte(File image) async {
    final InputImage inputImage = InputImage.fromFile(image);

    try {
      final RecognizedText recognizedText = await textRecognizer.processImage(inputImage);
      final Map<String, String?> infos = extraireInfosPokemon(recognizedText);

      final String? idTrouve = infos['identifier']; // Exemple: "BLK" ou "Démétéros"
      final String? numTrouve = infos['numero']; // Exemple: "131/086"

      setState(() {
        _isScanning = false;

        if (numTrouve != null) {
          final String rechercheNom = idTrouve ?? "Pokemon";
          _resultatScan = "✅ Analyse OCR !\nRecherche : $rechercheNom $numTrouve";
          ouvrirCardmarketPrecis(rechercheNom, numTrouve);
        } else {
          _resultatScan = "❌ Numéro introuvable.\n\n💡 Essayez le scan IA pour plus de précision.";
        }
      });
    } catch (e) {
      setState(() {
        _isScanning = false;
        _resultatScan = "❌ Erreur : $e";
      });
    }
  }
  
  // Placeholder: à remplacer par l'appel réel à Cardmarket
  void ouvrirCardmarketPrecis(String nom, String numero) {
    tool.ouvrirCardmarketPrecis(nom, numero);
  }

  @override
  void dispose() {
    textRecognizer.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scanner de Carte')),
      body: Column(
        children: [
          Expanded(
            flex: 2,
            child: _imagePrise != null
                ? Image.file(_imagePrise!)
                : Container(
                    color: Colors.grey[200],
                    child: const Center(
                      child: Icon(Icons.camera_alt, size: 50, color: Colors.grey),
                    ),
                  ),
          ),
          Expanded(
            flex: 1,
            child: Center(
              child: _isScanning
                  ? const CircularProgressIndicator()
                  : Text(
                      _resultatScan,
                      style: const TextStyle(fontSize: 18),
                      textAlign: TextAlign.center,
                    ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20.0),
            child: Column(
              children: [
                // Bouton Prendre Photo
                ElevatedButton.icon(
                  onPressed: prendrePhoto,
                  icon: const Icon(Icons.camera),
                  label: const Text('Prendre une photo'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 50),
                    backgroundColor: Colors.blue,
                  ),
                ),
                const SizedBox(height: 10),
                
                // Bouton Scan OCR
                ElevatedButton.icon(
                  onPressed: _imagePrise == null ? null : scannerAvecOCR,
                  icon: const Icon(Icons.text_fields),
                  label: const Text('Scan OCR (Rapide)'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 50),
                    backgroundColor: Colors.green,
                  ),
                ),
                const SizedBox(height: 10),
                
                // Bouton Scan IA
                ElevatedButton.icon(
                  onPressed: _imagePrise == null ? null : scannerAvecIA,
                  icon: const Icon(Icons.psychology),
                  label: const Text('Scan IA (Précis)'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 50),
                    backgroundColor: Colors.deepPurple,
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

Map<String, String?> extraireInfosPokemon(RecognizedText text) {
  // --- DEBUG ---
  print("Analyse OCR en cours...");
  print("\n========================================");
  print("CE QUE L'OCR VOIT (Ligne par ligne) :");
  print("========================================");
  
  // On parcourt tout le texte brut pour l'afficher
  int i = 0;
  for (TextBlock block in text.blocks) {
    for (TextLine line in block.lines) {
      i++;
      // J'ajoute des guillemets '' pour voir s'il y a des espaces invisibles
      print("Ligne #$i : '${line.text}'"); 
    }
  }
  print("========================================\n");
  String? nomPotentiel;
  String? codeExtensionPotentiel;
  String? numeroTrouve;

  // 1. D'ABORD LE NOM (Haut de la carte)
  // On le cherche en premier pour l'avoir en réserve
  int linesChecked = 0;
  for (TextBlock block in text.blocks) {
    for (TextLine line in block.lines) {
      linesChecked++;
      if (linesChecked > 6) break; // On ne regarde que le tout début

      String ligne = line.text.trim();
      String upper = ligne.toUpperCase();

      // LISTE NOIRE : Mots à bannir absolument
      if (upper.contains("PV") || 
          upper.contains("HP") || 
          upper == "BAS" ||   // <--- AJOUTÉ : C'était ton erreur !
          upper == "BASE" ||
          upper == "BASS" ||
          upper == "EBASE" ||
          upper == "<" ||
          upper.contains("NIVEAU") ||
          upper.contains("NIEAU") ||  // <--- Spécial pour ton bug
          upper.contains("EVOLUTION") ||
          upper.contains("ÉVOLUTION") ||
          // Si le mot commence par "NI" et fait moins de 7 lettres (souvent Niveau/Niv)
          (upper.startsWith("NIV") && upper.length < 8) || 
          // Si la ligne contient des chiffres isolés (ex: "50" pour les PV ou le niveau)
          RegExp(r'\b\d+\b').hasMatch(upper)) {
        continue;
      }

      // Si c'est un mot de plus de 3 lettres qui a survécu au filtre
      if (nomPotentiel == null && ligne.length > 2) {
        nomPotentiel = ligne;
        print("Candidat Nom trouvé : $nomPotentiel");
      }
    }
  }

  // 2. ENSUITE LE NUMÉRO & LE CODE (Bas de la carte)
  List<TextBlock> blocsInverses = List.from(text.blocks.reversed);

  // Regex : "131" + séparateur + "086"
  final RegExp regexNumero = RegExp(r'\b([A-Z0-9]{1,5})\s*[\/|\\I]\s*([A-Z0-9]{2,5})\b');
    // Sécurité : Un vrai numéro doit contenir au moins un chiffre (0-9)
  // Ça évite de prendre "BLK/FR" pour un numéro
  final RegExp contientChiffre = RegExp(r'[0-9]'); 
  // Regex : Code de 3 ou 4 lettres MAJUSCULES (ex: BLK, DBUS, SWSH)
  final RegExp regexCode = RegExp(r'\b[A-Z0-9]{3,4}\b');
  

  for (TextBlock block in blocsInverses) {
    for (TextLine line in block.lines) {
      String ligne = line.text.trim();
      
      // On teste le regex
      RegExpMatch? match = regexNumero.firstMatch(ligne);
      
      if (match != null) {
        String partie1 = match.group(1)!;
        String partie2 = match.group(2)!;
        String candidatNumero = "$partie1/$partie2";

        // VÉRIFICATION DE SÉCURITÉ
        // 1. Est-ce qu'il y a au moins un chiffre ? (Evite "ABC/DEF")
        // 2. Est-ce que ce n'est pas une année ? (Evite "2020/2024")
        if (contientChiffre.hasMatch(candidatNumero) && 
            !candidatNumero.startsWith("202")) { // Filtre basique anti-année copyright
          
           numeroTrouve = candidatNumero;
           print("🎯 Numéro VALIDÉ et Nettoyé : $numeroTrouve");
           
           // ... (Ici tu peux mettre ta logique pour chercher le code BLK à côté) ...
           
           break; // On a trouvé, on sort !
        } else {
           print("Poubelle (Faux positif) : $candidatNumero");
        }
      }
    }
    if (numeroTrouve != null) break;
  }

  // --- 3. DÉCISION FINALE (Le Cerveau) ---
  String identifierFinal;

  if (numeroTrouve != null) {
    // Stratégie : Le NOM est souvent plus fiable pour la recherche Cardmarket 
    // que le code extension mal lu par l'OCR ("DBUS" au lieu de "BLK").
    // Cardmarket gère très bien "Demeteros 131/086".
    // Cardmarket ne trouvera RIEN avec "DBUS 131/086".
    
    if (nomPotentiel != null) {
      identifierFinal = nomPotentiel; // On privilégie "Demétéros"
    } else if (codeExtensionPotentiel != null) {
      identifierFinal = codeExtensionPotentiel; // Sinon on tente le code "DBUS"
    } else {
      identifierFinal = "Pokemon"; // Fallback total
    }
  } else {
    identifierFinal = "Inconnu";
  }

  print("👉 CHOIX FINAL -> $identifierFinal $numeroTrouve");

  return {
    'identifier': identifierFinal,
    'numero': numeroTrouve
  };
}