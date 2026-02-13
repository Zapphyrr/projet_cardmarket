# Copilot Instructions - Projet CardMarket Pokemon

## Project Overview
Pokemon card scanner mobile app that uses OCR to identify cards and open their Cardmarket.com listings. The app scans Pokemon cards, extracts card name and number, then intelligently searches Cardmarket with language filtering for French market prices.

**Architecture:**
- **Flutter app** (`flutter_application_1/`): Mobile UI with camera scanning
- **Python scripts** (root level): Data processing and prototyping
- **Pokemon TCG data** (`pokemon-tcg-data-master/`, `pokemon_db_light.json`): Card database source

## Core Workflow

### Card Scanning Flow
1. User takes photo via `ScannerScreen` → `prendrePhoto()`
2. ML Kit OCR processes image → `analyserTexte()`
3. `extraireInfosPokemon()` parses OCR text using **specific logic**:
   - Searches **top 6 lines** for card name, filtering out "PV", "HP", "NIVEAU", "BAS", "BASE"
   - Searches **bottom-up** for card number using regex `\b([A-Z0-9]{1,5})\s*[\/|\\I]\s*([A-Z0-9]{2,5})\b`
   - **Prefers card NAME over set code** for Cardmarket search (more reliable than misread codes)
4. `ouvrirCardmarketPrecis()` searches Cardmarket, handles redirects, applies `?language=2` filter

### Cardmarket Integration Strategy
**Critical:** Cardmarket blocks standard HTTP clients (403 errors). Current workaround:
- Use realistic browser headers (`User-Agent`, `Accept-Language`)
- Let `http.get()` follow redirects naturally
- Open final URL in **external browser** (`LaunchMode.externalApplication`) to bypass bot detection
- See `tools.dart` lines 35-95 for full implementation

### Data Processing
- `json_to_bd.py`: Consolidates Pokemon TCG JSON files into `pokemon_db_light.json`
- Extracts: `id`, `name`, `number`, `set_id`, `image`, `cm_url`, `release_date`, `set_name`, `ip_set_card`
- Uses `sets_dict` for O(1) set metadata lookup via `en.json`

## Development Commands

### Flutter
```bash
# Navigate to app directory first
cd flutter_application_1

# Run on connected device/emulator
flutter run

# Build release APK (Android)
flutter build apk --release

# Install dependencies
flutter pub get

# Hot reload: Press 'r' in terminal while app running
# Hot restart: Press 'R' (capital) in terminal
```

### Python Data Processing
```bash
# Activate virtual environment (if exists)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Regenerate lightweight card database
python json_to_bd.py

# Test Cardmarket scraping (prototyping)
python test_local.py
```

## Project-Specific Conventions

### OCR Text Extraction Rules (`scanner_screen.dart` lines 127-190)
- **Name extraction blacklist**: PV, HP, BAS, BASE, BASS, NIEAU, NIVEAU, EVOLUTION
- Reject lines containing isolated numbers (likely PV values, not names)
- Card number MUST contain at least one digit (prevents "BLK/FR" false positives)
- Filters out copyright years starting with "202"

### Cardmarket URL Construction Pattern
```dart
// Always append language filter for French market
"${baseUrl.split('?')[0]}?language=2"

// Handle two scenarios:
// 1. /Search URL (multiple results) → add &language=2
// 2. /Products/Singles URL (direct) → add ?language=2
```

### Flutter Dependencies (see `pubspec.yaml`)
- `google_mlkit_text_recognition`: OCR engine
- `url_launcher`: Opens Cardmarket in external browser
- `http`: Network requests with redirect following
- `image_picker`: Camera access
- Asset bundled: `assets/pokemon_db_light.json`

## Key Files & Their Roles

- [`lib/scanner_screen.dart`](flutter_application_1/lib/scanner_screen.dart): Camera UI, OCR processing, text parsing logic
- [`lib/tools.dart`](flutter_application_1/lib/tools.dart): Cardmarket API/scraping functions, URL handling
- [`lib/main.dart`](flutter_application_1/lib/main.dart): App entry point, theme configuration (red accent color)
- [`json_to_bd.py`](json_to_bd.py): Batch processor for Pokemon TCG data consolidation
- [`test_local.py`](test_local.py): Python prototyping for Cardmarket scraping strategies
- [`pokemon_db_light.json`](pokemon_db_light.json): Compiled card database (generated, not edited directly)

## Common Pitfalls

1. **Cardmarket 403 errors**: Don't use simple `http.get()` without proper headers. Must simulate browser behavior.
2. **OCR false positives**: Always validate extracted numbers contain digits. The string "BAS" commonly misread as card name.
3. **Flutter asset changes**: After modifying `pubspec.yaml` assets, run `flutter pub get` before testing.
4. **Python scripts location**: Run data scripts from **root directory**, not from `flutter_application_1/`.
5. **External browser requirement**: `LaunchMode.inAppWebView` will fail on Cardmarket due to bot detection.

## Testing Strategy

- **OCR accuracy**: Test with physical cards at different angles/lighting
- **Cardmarket search**: Verify both direct product hits and multi-result pages
- **Edge cases**: Cards with special characters (é, è), trainer cards, promo numbers (e.g., "TG05/TG30")
- **Python data**: Verify `pokemon_db_light.json` has expected card count after regeneration
