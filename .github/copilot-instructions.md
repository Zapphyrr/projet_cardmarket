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

---

## API Architecture (Flask + Railway Deployment)

### Overview
Cloud-based card recognition API using **ORB feature detection + FLANN matching** to identify Pokemon cards from photos. Hosted on **Railway.app** with 1GB RAM.

**Why an API?**
- Offload heavy image processing from mobile devices
- Centralized database updates (no app resubmission)
- Faster processing on server hardware
- Cross-platform support (Flutter, Python, web)

### Technical Stack

**Backend:**
- **Flask 3.0.0**: Lightweight Python web framework
- **OpenCV 4.9.0**: Computer vision library (ORB, FLANN)
- **Gunicorn**: Production WSGI server with multi-threading
- **Flask-CORS**: Enable cross-origin requests from Flutter
- **gdown 5.2.0**: Download database from Google Drive at startup

**Computer Vision:**
- **ORB (Oriented FAST and Rotated BRIEF)**: Binary feature detector
- **FLANN (Fast Library for Approximate Nearest Neighbors)**: LSH-based indexing
- **KNN (K-Nearest Neighbors)**: K=2 for Lowe's ratio test

**Database:**
- `orb_db.pkl`: Pickled Python dict with 19,783 cards
- Each card: `{'id': 'number-name-set', 'descriptors': np.array (uint8)}`
- Hosted on Google Drive (bypasses Railway storage limits)
- Size: ~140-150MB with 50 features, ~90-100MB with 30 features

### Key Files (API)

#### [`lib_python_sandbox/api_server.py`](lib_python_sandbox/api_server.py)
Main Flask application with endpoints:
- **GET `/health`**: Returns `{"status": "ok", "cartes_loaded": 19783}`
- **POST `/search`**: Accepts base64 image, returns card info

**Startup sequence:**
1. Downloads `orb_db.pkl` from Google Drive (if not cached)
2. Loads 19,783 cards into memory (~150MB RAM)
3. Builds super_matrix (vstack of all descriptors)
4. Initializes FLANN matcher with LSH index
5. Starts Gunicorn workers

**Processing pipeline (per request):**
1. Decode base64 image → PIL Image → grayscale numpy array
2. Resize to max 300px (reduce processing time)
3. ORB feature extraction (50 keypoints)
4. FLANN knnMatch (k=2) against super_matrix
5. Lowe's ratio test (0.75) to filter ambiguous matches
6. Vote counting: card with most good matches wins
7. Return JSON: `{"carte": "123-Pikachu-Base", "score": 45, ...}`

#### [`lib_python_sandbox/finger_print_quick.py`](lib_python_sandbox/finger_print_quick.py)
Database generator: Downloads 19,783 card images from URLs, computes ORB descriptors, saves to `orb_db.pkl`.

**Configuration:**
```python
orb = cv2.ORB_create(nfeatures=50)  # 50 features per card
```

**Multi-threaded:** 50 workers process images in parallel (~10-15 min to complete).

#### [`lib_python_sandbox/recherche_cartes_api.py`](lib_python_sandbox/recherche_cartes_api.py)
Python test client: Sends image to API, measures response time, opens Cardmarket.

**Usage:**
```python
API_URL = "https://projectcardmarket-production.up.railway.app"
carte_trouvée = trouver_carte_via_api("templates/locklass.png")
```

#### [`flutter_application_1/lib/api_service.dart`](flutter_application_1/lib/api_service.dart)
Flutter HTTP client for calling the API from the mobile app.

**Usage:**
```dart
final result = await CardRecognitionAPI.searchCard(imageFile);
if (result != null) {
  print("Carte trouvée: ${result['carte']}");
}
```

### Deployment Configuration

#### [`lib_python_sandbox/Procfile`](lib_python_sandbox/Procfile)
```
web: gunicorn api_server:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 4 --worker-class gthread --max-requests 100 --max-requests-jitter 10
```

**Optimizations for 1GB RAM:**
- `--workers 1`: Single worker process (saves ~400MB vs 2 workers)
- `--threads 4`: Multi-threading for concurrent requests
- `--worker-class gthread`: Thread-based concurrency
- `--max-requests 100`: Restart worker every 100 requests (prevent memory leaks)
- `--timeout 120`: 2-minute timeout for slow requests

#### [`lib_python_sandbox/requirements.txt`](lib_python_sandbox/requirements.txt)
```
flask==3.0.0
flask-cors==4.0.0
gunicorn==21.2.0
opencv-python-headless==4.9.0.80  # Headless = no GUI, smaller
numpy==1.26.4
Pillow==10.2.0
gdown==5.2.0
requests==2.31.0
```

#### [`lib_python_sandbox/runtime.txt`](lib_python_sandbox/runtime.txt)
```
python-3.11.9
```
**Important:** Python 3.14 has build issues with Pillow/numpy. Use 3.11.x.

#### [`railway.toml`](railway.toml)
Railway-specific configuration for deployment from subdirectory:
```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r lib_python_sandbox/requirements.txt"

[deploy]
startCommand = "cd lib_python_sandbox && gunicorn api_server:app --bind 0.0.0.0:$PORT ..."
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

### Environment Variables (Railway Settings)

**Required:**
- `ORB_DB_GDRIVE_ID`: Google Drive file ID for `orb_db.pkl`
  - Format: `https://drive.google.com/file/d/FILE_ID_HERE/view`
  - Example: `1WJwcUECUFG6i60JqZJeXibyx8xDCq3QE`

**Automatic:**
- `PORT`: Railway assigns dynamically (usually 8080)

### Performance Metrics

**Local (Python script with orb_db.pkl):**
- Initial: 20-28 seconds
- After optimizations: 8-10 seconds

**API (Railway 1GB RAM with 50 features):**
- Target: 2-5 seconds
- Actual: 1.5s for small images, **10-60s or timeout for complex images** ⚠️

**Bottleneck:** FLANN knnMatch on super_matrix (1M+ descriptors) consumes 300-500MB RAM spike.

---

## Computer Vision Technical Details

### ORB (Oriented FAST and Rotated BRIEF)

**Type:** Classical computer vision algorithm (NOT deep learning/AI)

**How it works:**
1. **FAST**: Detects corner points (keypoints) in the image
2. **BRIEF**: Generates binary descriptor (256 bits / 32 bytes) for each keypoint
3. **Oriented**: Adds rotation invariance (card can be tilted)

**Advantages:**
- ✅ Fast: 100x faster than SIFT/SURF
- ✅ Lightweight: Binary descriptors (uint8) vs float32
- ✅ No training required: Works immediately
- ✅ Rotation/scale invariant

**Configuration:**
```python
orb = cv2.ORB_create(nfeatures=50)
kp, des = orb.detectAndCompute(image_gray, None)
# des.shape = (50, 32) = 1.6KB per card
```

**Trade-off:** Fewer features = faster but less accurate
- **500 features**: Very accurate, 8KB/card, slow matching
- **100 features**: Good balance, 3.2KB/card
- **50 features**: Fast, 1.6KB/card, sufficient for distinctive cards
- **30 features**: Ultra-fast, 960B/card, risk of false negatives

### FLANN (Fast Library for Approximate Nearest Neighbors)

**Purpose:** Index and search 19,783 cards × 50 features = ~990K descriptors in <5 seconds

**Algorithm:** LSH (Locality-Sensitive Hashing) for binary descriptors

**How LSH works:**
1. Hash each 256-bit descriptor to short hash codes (6-12 bits)
2. Group similar descriptors into "buckets"
3. Query only searches within matching buckets (~0.1% of database)
4. Returns approximate nearest neighbors (not exact, but 95%+ accurate)

**Configuration:**
```python
index_params = dict(
    algorithm=6,          # LSH for binary descriptors
    table_number=1,       # 1 hash table (RAM optimization)
    key_size=6,           # 6-bit hash keys
    multi_probe_level=0   # Direct lookup only
)
search_params = dict(checks=1)  # Minimal verification
matcher = cv2.FlannBasedMatcher(index_params, search_params)
```

**RAM optimization:** Reducing `table_number` and `key_size` saves memory but marginally reduces accuracy.

### KNN + Lowe's Ratio Test

**KNN (K-Nearest Neighbors):** For each query feature, find the 2 best matches in the database.

**Why k=2?** Lowe's ratio test needs 2nd-best match to assess confidence:

```python
matches = matcher.knnMatch(query_descriptors, k=2)

for m, n in matches:  # m = best, n = 2nd-best
    if m.distance < 0.75 * n.distance:  # Best is 25% better than 2nd
        good_matches.append(m)  # High confidence match
    # Otherwise: ambiguous, reject
```

**Ratio 0.75:** Standard threshold from Lowe's paper. Lower = stricter.

**Distance metric:** Hamming distance (count differing bits between binary descriptors)

### Complete Workflow

```
1. User photo (3024×4032 pixels)
      ↓
2. Resize to 300px max dimension (speed optimization)
      ↓
3. Convert to grayscale (1 channel vs 3)
      ↓
4. ORB.detectAndCompute() → 50 keypoints × 256 bits
      ↓
5. FLANN.knnMatch() → LSH lookup in super_matrix
      ↓ ~2-10 seconds (bottleneck)
6. KNN returns 50 × 2 = 100 candidate matches
      ↓
7. Ratio test (0.75) → filters to ~20-40 good matches
      ↓
8. Vote counting → card_id with most matches wins
      ↓
9. Return card_id: "025-Pikachu-Base1"
```

---

## Deployment Issues & Solutions

### Issue 1: Out of Memory (512MB Render / 1GB Railway)

**Symptoms:**
- Worker starts, loads database (150MB), then crashes with `SIGKILL`
- Health endpoint works, but `/search` times out or crashes
- Logs show: `[ERROR] Worker was sent SIGKILL! Perhaps out of memory?`

**Root cause:**
- Database: 150MB (with 50 features)
- OpenCV/NumPy libraries: 120MB
- Flask + Gunicorn: 180MB
- **FLANN knnMatch** temporary buffers: **300-500MB spike** 💥
- **Total: 750-950MB** → exceeds 1GB limit

**Solutions tried:**
1. ✅ Reduced workers from 2 to 1 (saves 400MB)
2. ✅ Reduced ORB features: 500 → 100 → 50 (database 280MB → 150MB)
3. ⚠️ Reduce to 30 features (database ~90MB, untested)
4. ❌ BFMatcher instead of FLANN (assertion error with large DB)
5. 💵 Upgrade to 2GB RAM (Railway $10-12/month, DigitalOcean $25/month)

**Current status:** 50 features works intermittently on Railway 1GB, but unstable under load.

### Issue 2: Railway Port Binding

**Symptoms:** Server starts, logs show "Listening at 127.0.0.1:8000", but health check fails.

**Root cause:** Gunicorn not binding to Railway's dynamic `$PORT` variable.

**Solution:** Add `--bind 0.0.0.0:$PORT` to Procfile:
```
web: gunicorn api_server:app --bind 0.0.0.0:$PORT ...
```

### Issue 3: Python 3.14 Compatibility

**Symptoms:** Build fails with "Failed to build Pillow" or numpy errors.

**Root cause:** Python 3.14 is too new, C extensions don't compile.

**Solution:** Force Python 3.11.9 via `runtime.txt`:
```
python-3.11.9
```

### Issue 4: Google Drive Rate Limiting

**Symptoms:** `gdown` fails with "quota exceeded" or "too many requests".

**Solution:**
- Make `orb_db.pkl` public (Share → Anyone with link)
- Use direct download link format: `https://drive.google.com/uc?id=FILE_ID`
- Cache file locally after first download (Railway persistent disk)

### Issue 5: Timeout on /search Endpoint

**Symptoms:** `/health` works instantly, `/search` times out after 30-60s.

**Root cause:** Image processing + FLANN matching takes 10-60s with 50 features on 1GB RAM.

**Solutions:**
1. Increase client timeout to 60s (done in `recherche_cartes_api.py`)
2. Add debug logs to track bottleneck (image decode vs ORB vs FLANN)
3. Reduce features to 30 (untested)
4. Implement caching for repeated queries

---

## API Usage Examples

### Python Client

```python
import requests
import base64

API_URL = "https://projectcardmarket-production.up.railway.app"

# Load and encode image
with open("carte.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# Send to API
response = requests.post(
    f"{API_URL}/search",
    json={"image": image_base64},
    timeout=60
)

if response.status_code == 200:
    data = response.json()
    print(f"Carte: {data['carte']}")
    print(f"Score: {data['score']}")
else:
    print(f"Erreur: {response.status_code}")
```

### Flutter Client

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

final imageBytes = await File('carte.jpg').readAsBytes();
final base64Image = base64Encode(imageBytes);

final response = await http.post(
  Uri.parse('https://projectcardmarket-production.up.railway.app/search'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({'image': base64Image}),
);

if (response.statusCode == 200) {
  final data = jsonDecode(response.body);
  print('Carte: ${data['carte']}');
}
```

### cURL

```bash
# Health check
curl https://projectcardmarket-production.up.railway.app/health

# Search (with base64 image)
curl -X POST https://projectcardmarket-production.up.railway.app/search \
  -H "Content-Type: application/json" \
  -d '{"image": "iVBORw0KGgoAAAA..."}'
```

---

## Optimization History

### ORB Features Reduction
| Features | DB Size | Local Speed | API Speed | Accuracy |
|----------|---------|-------------|-----------|----------|
| 500 | ~280MB | 28s | N/A | Excellent |
| 100 | ~150MB | 12s | Timeout | Very Good |
| 50 | ~90MB | 10s | 1.5-60s | Good |
| 30 | ~60MB | 8s | Untested | Fair |

### FLANN Parameters Evolution
```python
# Initial (accurate but slow)
table_number=6, key_size=12, checks=50

# Optimized for speed
table_number=2, key_size=8, checks=1

# RAM-constrained (Railway 1GB)
table_number=1, key_size=6, checks=1, multi_probe_level=0
```

### Image Preprocessing
- Max dimension: 800px → 400px → 300px (speed vs quality trade-off)
- Grayscale conversion: Reduces data by 67% (RGB → 1 channel)

---

## Next Steps / TODO

**High Priority:**
- [ ] Test 30-feature configuration on Railway (reduce RAM usage)
- [ ] Implement response caching for identical images
- [ ] Add request rate limiting (prevent abuse)
- [ ] Monitor Railway metrics (RAM usage, response times)

**Medium Priority:**
- [ ] Integrate API into Flutter app (replace local OCR)
- [ ] A/B test: OCR (fast, inaccurate) vs API (slow, accurate)
- [ ] Add confidence threshold parameter to API
- [ ] Implement batch processing endpoint (multiple images)

**Low Priority:**
- [ ] Explore DigitalOcean 2GB droplet ($25/month for better performance)
- [ ] Optimize super_matrix construction (lazy loading?)
- [ ] Add Prometheus metrics endpoint
- [ ] Implement image preprocessing recommendations (white balance, contrast)

---

## Troubleshooting Guide

**Problem:** Railway deployment fails with "Build error"
- Check `runtime.txt` specifies Python 3.11.x (not 3.14)
- Verify all dependencies in `requirements.txt` are compatible
- Check Railway build logs for specific error messages

**Problem:** Server starts but health check returns 404
- Verify Railway domain is correct (check Settings → Domains)
- Check Procfile uses `--bind 0.0.0.0:$PORT`
- Ensure `railway.toml` points to correct directory

**Problem:** `/search` endpoint times out
- Check Railway logs for "out of memory" errors
- Verify `orb_db.pkl` downloaded successfully (check file size in logs)
- Increase client timeout to 60+ seconds
- Consider reducing features to 30

**Problem:** All matches rejected (score = 0)
- Image too blurry or small (< 200px)
- Card not in database (check `pokemon_card_bdd.csv`)
- Try lowering ratio test threshold (0.75 → 0.8)

**Problem:** Wrong card identified
- Increase features (30 → 50) for better discrimination
- Check if database has duplicate/similar card images
- Verify card number format in database matches query

---

## References & Resources

**Computer Vision:**
- [ORB Paper](https://www.willowgarage.com/sites/default/files/orb_final.pdf): Original algorithm description
- [FLANN Documentation](https://docs.opencv.org/4.x/d5/d6f/tutorial_feature_flann_matcher.html): OpenCV FLANN guide
- [Lowe's Ratio Test](https://www.cs.ubc.ca/~lowe/papers/ijcv04.pdf): SIFT paper (section 7.1)

**Deployment:**
- [Railway Documentation](https://docs.railway.app/): Deployment guides
- [Gunicorn Settings](https://docs.gunicorn.org/en/stable/settings.html): Worker configuration
- [Flask Best Practices](https://flask.palletsprojects.com/en/3.0.x/deploying/): Production deployment

**Pokemon TCG Data:**
- [Pokemon TCG API](https://pokemontcg.io/): Official card database
- [Cardmarket](https://www.cardmarket.com/fr/Pokemon): Price marketplace

---

## Contact & Support

**Project Repository:** [Zapphyrr/projet_cardmarket](https://github.com/Zapphyrr/projet_cardmarket)

**Railway Deployment:** [projectcardmarket-production.up.railway.app](https://projectcardmarket-production.up.railway.app)

**Google Drive Database:** Hosted privately, download via `gdown` in API server

For questions or issues, refer to this document or consult GitHub Copilot in VS Code.
