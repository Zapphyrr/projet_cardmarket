import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'scanner_screen.dart';
import 'tools.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter',
      theme: ThemeData(
        // This is the theme of your application.
        //
        // TRY THIS: Try running your application with "flutter run". You'll see
        // the application has a purple toolbar. Then, without quitting the app,
        // try changing the seedColor in the colorScheme below to Colors.green
        // and then invoke "hot reload" (save your changes or press the "hot
        // reload" button in a Flutter-supported IDE, or press "r" if you used
        // the command line to start the app).
        //
        // Notice that the counter didn't reset back to zero; the application
        // state is not lost during the reload. To reset the state, use hot
        // restart instead.
        //
        // This works for code too, not just values: Most code changes can be
        // tested with just a hot reload.
        colorScheme: ColorScheme.fromSeed(seedColor: const Color.fromARGB(255, 209, 4, 4)),
      ),
      home: const ScannerScreen(),
     
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  // This widget is the home page of your application. It is stateful, meaning
  // that it has a State object (defined below) that contains fields that affect
  // how it looks.

  // This class is the configuration for the state. It holds the values (in this
  // case the title) provided by the parent (in this case the App widget) and
  // used by the build method of the State. Fields in a Widget subclass are
  // always marked "final".

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {

  @override
  Widget build(BuildContext context) {
    // This method is rerun every time setState is called, for instance as done
    // by the _incrementCounter method above.
    //
    // The Flutter framework has been optimized to make rerunning build methods
    // fast, so that you can just rebuild anything that needs updating rather
    // than having to individually change instances of widgets.
    return Scaffold(
      appBar: AppBar(
        // TRY THIS: Try changing the color here to a specific color (to
        // Colors.amber, perhaps?) and trigger a hot reload to see the AppBar
        // change color while the other colors stay the same.
        backgroundColor: Theme.of(context).colorScheme.primary,
        // Here we take the value from the MyHomePage object that was created by
        // the App.build method, and use it to set our appbar title.
        title: Text(widget.title),
      ),
      body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                'Test de redirection Cardmarket',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 20),
              // LE BOUTON
              ElevatedButton.icon(
                onPressed: () async {
                  // 1. On récupère l'URL propre (ça peut prendre 1 seconde, d'où le await)
                  String? urlPropre = await ouvrirCardmarketPrecis("test", "test"); // Exemple ID Zekrom

                  // 2. Si on a bien récupéré l'URL, on l'ouvre
                  if (urlPropre != null) {
                    final Uri uri = Uri.parse(urlPropre);
                    // On ouvre dans le navigateur externe (Chrome/Safari)
                    // C'est ici que le Plan B1 prend tout son sens : pas de blocage 403 !
                    await launchUrl(uri, mode: LaunchMode.externalApplication); 
                  } else {
                    // Affiche un petit message d'erreur (SnackBar) si ça échoue
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Impossible de récupérer le lien Cardmarket')),
                    );
                  }
                },
                icon: const Icon(Icons.open_in_browser),
                label: const Text('Voir le prix de Zekrom'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                ),
              ),
            ],
          ),
        ),
    );
  }
}