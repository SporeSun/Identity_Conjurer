
# 🧙 Identity Conjurer

A Flask-powered web application that generates *fictional identities built on real-world OpenStreetMap data.*

It combines a random name generator with **verified, mapped street addresses** from OpenStreetMap, producing realistic output for testing, prototyping, or creative projects.

---

## ✨ Features

* 🧠 Random human-style names (Modern, Fantasy, Sci-Fi, or Silly themes)
* 🏙️ **Real existing addresses** using OpenStreetMap’s `addr:housenumber` and `addr:street` tags
* 🌎 Works globally — city, state, ZIP, or country queries
* ⚡ Web UI and REST API
* 🔁 Auto-detects open port (5000–5100)
* 🧩 Self-contained — no database required

---

## 🧰 Tech Stack

* **Python 3.9+**
* **Flask** — lightweight web framework
* **Requests** — handles API communication with OSM, Overpass, and Nominatim

---

## 📦 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourname/identity-conjurer.git
cd identity-conjurer
```

### 2️⃣ Create a virtual environment (optional)

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install flask requests
```

---

## 🚀 Usage

### Run the app

```bash
python identity_conjurer.py
```

You’ll see:

```
🧙 Identity Conjurer running on port 5000 ...
 * Running on http://127.0.0.1:5000
```

### Open in browser

Go to **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

Enter a ZIP code or city/state/country, choose a name style, and click **Conjure Identity 🪄**

---

## 🧪 Example Output

```
Name: Emma Garcia
Street Address: 42 Camino Capistrano
City, State, ZIP: San Juan Capistrano, California 92675
```

---

## 🔗 API Usage

### Endpoint

```
GET /api
```

### Parameters

| Parameter  | Description                                         | Default         |
| ---------- | --------------------------------------------------- | --------------- |
| `theme`    | Name theme (`modern`, `fantasy`, `sci-fi`, `silly`) | `modern`        |
| `location` | City, state, country, or ZIP code                   | `New York, USA` |

### Example Request

```bash
curl "http://127.0.0.1:5000/api?theme=fantasy&location=90210"
```

### Example Response

```json
{
  "name": "Thrain Dawnspire",
  "street": "2715 Rodeo Dr",
  "city": "Beverly Hills",
  "state": "California",
  "zip": "90210"
}
```

---

## ⚠️ Notes & Limitations

* Only areas with **mapped building-level addresses** appear; otherwise the app returns
  `Error: No real addresses found in this area.`
* Results are genuine OpenStreetMap data, not guaranteed complete or up to date.
* Follow [OpenStreetMap’s Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/):

  > Include a valid User-Agent and avoid sending excessive automated requests.

---

## 🧙‍♂️ Project Structure

```
identity-conjurer/
├── identity_conjurer.py   # main Flask application
├── cache.json             # (auto-generated) cached OSM results
└── README.md
```

---

## 🌍 How It Works

1. **Geocoding:** Nominatim converts the user’s location (ZIP, city, etc.) into a geographic bounding box.
2. **Address Query:** Overpass API searches for OSM nodes tagged with `addr:housenumber` and `addr:street` inside that box.
3. **Selection:** The app picks a random real address from the results.
4. **Reverse Geocoding:** Nominatim reverse-geocodes the coordinate to extract `city`, `state`, and `postcode`.
5. **Identity Assembly:** A themed random name is paired with the real-world address.

---

## 🧩 Customization Ideas

* 🧱 Add synthetic fallback when no real addresses exist.
* 🗺️ Integrate a Leaflet.js map showing the generated address pin.
* 📦 Export generated identities to CSV or JSON.
* 🧑‍🎨 Combine with AI-generated portraits for mock user data.

---

## ☁️ Deployment

You can easily deploy **Identity Conjurer** on platforms like:

* [Render](https://render.com/)
* [Railway](https://railway.app/)
* [Replit](https://replit.com/)
* [Fly.io](https://fly.io/)

Just set the start command to:

```bash
python identity_conjurer.py
```

---

## 🪄 License

MIT License — use freely for research, development, or creative projects.

© 2025 Your Name.
Built with OpenStreetMap data