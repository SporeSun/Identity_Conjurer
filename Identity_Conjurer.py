from flask import Flask, request, jsonify, render_template_string
import requests
import random
import json
import os
import socket
import re

app = Flask(__name__)

# ---------------- CONFIG -----------------
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "IdentityConjurer/1.0 (contact@example.com)"}
CACHE_FILE = "cache.json"

# -----------------------------------------
# -------- UTILITY FUNCTIONS --------------

def get_free_port(start=5000, end=5100):
    """Finds first available TCP port in range."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise OSError(f"No free ports found between {start}-{end}")

# --------------- CACHE -------------------
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

# --------- NAME GENERATOR ---------------

FIRST_NAMES = {
    "modern": ["Emma", "Liam", "Olivia", "Noah", "Sophia", "Mason", "Ava", "Ethan", "Isabella", "Lucas"],
    "fantasy": ["Elora", "Thrain", "Mirael", "Gorath", "Elandra", "Fenric", "Kael", "Seraphine", "Tovin", "Lira"],
    "sci-fi": ["Nova", "Zyra", "Orion", "Kaon", "Vex", "Astra", "Rho", "Nyx", "Ceres", "Dray"],
    "silly": ["Pickle", "Snorf", "Bloop", "Wumbo", "Tater", "Flibber", "Muffin", "Doodle", "Crumpet", "Bonk"]
}

LAST_NAMES = {
    "modern": ["Johnson", "Smith", "Brown", "Garcia", "Martinez", "Lee", "Davis", "Clark", "Miller", "Taylor"],
    "fantasy": ["Stormforge", "Moonshadow", "Ironfist", "Silverleaf", "Windwalker", "Bloodfang", "Starwhisper", "Dawnspire"],
    "sci-fi": ["Prime", "NovaCore", "Sigma", "Void", "Axis", "Ion", "Nebula", "Chrome", "Pulse"],
    "silly": ["McNoodle", "Bumblefluff", "Wigglesworth", "Cheesebottom", "Snickerdoodle", "Boopington", "Flapjack"]
}

def generate_name(theme="modern"):
    if theme not in FIRST_NAMES:
        theme = "modern"
    first = random.choice(FIRST_NAMES[theme])
    last = random.choice(LAST_NAMES[theme])
    return f"{first} {last}"

# --------- ADDRESS GENERATOR ------------

def get_bounding_box(location):
    """Geocode location to get bounding box and metadata."""
    if location in cache:
        return cache[location]["bbox"], cache[location]["meta"]
    params = {"q": location, "format": "json", "limit": 1}
    response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError("Location not found.")
    bbox = [float(x) for x in data[0]["boundingbox"]]
    meta = data[0]
    cache[location] = {"bbox": bbox, "meta": meta}
    save_cache()
    return bbox, meta

def get_random_street_from_bbox(bbox):
    """Selects a random valid street name from Overpass data."""
    south, north, west, east = bbox
    query = f"""
    [out:json][timeout:25];
    (
      way["highway"~"residential|tertiary|secondary|primary"]["name"]({south},{west},{north},{east});
    );
    out tags;
    """
    response = requests.post(OVERPASS_URL, data=query, headers=HEADERS)
    response.raise_for_status()
    elements = response.json().get("elements", [])
    valid_streets = [e for e in elements if "name" in e["tags"]]
    if not valid_streets:
        raise ValueError("No valid streets found in this area.")
    random_street = random.choice(valid_streets)
    return random_street["tags"]["name"]

def generate_random_address(location_input):
    """Creates a random full address including city/state/zip, with fallback reverse lookup."""
    bbox, meta = get_bounding_box(location_input)
    street_name = get_random_street_from_bbox(bbox)
    house_number = random.randint(1, 9999)

    address_info = meta.get("address", {})

    # Fallback: if city/state missing, do reverse lookup
    if not address_info.get("city") and not address_info.get("state"):
        lat = (float(meta["boundingbox"][0]) + float(meta["boundingbox"][1])) / 2
        lon = (float(meta["boundingbox"][2]) + float(meta["boundingbox"][3])) / 2
        rev = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers=HEADERS
        )
        if rev.ok:
            rev_data = rev.json()
            if "address" in rev_data:
                address_info = rev_data["address"]

    city = (
        address_info.get("city")
        or address_info.get("town")
        or address_info.get("village")
        or address_info.get("hamlet")
        or "Unknown City"
    )
    state = address_info.get("state", "Unknown State")
    zip_code = address_info.get("postcode", "00000")

    return {
        "street": f"{house_number} {street_name}",
        "city": city,
        "state": state,
        "zip": zip_code
    }



# ----------- FLASK ROUTES --------------

@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Identity Conjurer</title>
      <style>
      
  body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(120deg, #7F7FD5, #86A8E7, #91EAE4); margin: 0; padding: 0; color: #333; }
        h1 { text-align: center; color: white; padding-top: 30px; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); }
        .container { width: 420px; margin: 40px auto; background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        select, input, button { width: 100%; padding: 10px; margin-top: 10px; border-radius: 8px; border: 1px solid #ccc; font-size: 1em; }
        button { background: #7F7FD5; color: white; font-weight: bold; border: none; cursor: pointer; transition: 0.3s; }
        button:hover { background: #6C6CCF; }
        .result { margin-top: 20px; text-align: center; font-weight: bold; }
        .label { font-size: 0.9em; color: #666; }
      </style>
    </head>
    <body>
      <h1>🧙 Identity Conjurer</h1>
      <div class="container">
        <form method="post" action="/generate">
          <label for="theme">Name Style:</label>
          <select id="theme" name="theme">
            <option value="modern">Modern</option>
            <option value="fantasy">Fantasy</option>
            <option value="sci-fi">Sci-Fi</option>
            <option value="silly">Silly</option>
          </select>
          <label for="location">Location (ZIP or City/State/Country):</label>
          <input type="text" id="location" name="location" placeholder="e.g. 92675 or Paris, France" required>
          <button type="submit">Conjure Identity 🪄</button>
        </form>
        {% if identity %}
        <div class="result">
          <p><span class="label">Name:</span><br>{{ identity.name }}</p>
          <p><span class="label">Street Address:</span><br>{{ identity.street }}</p>
          <p><span class="label">City, State, ZIP:</span><br>{{ identity.city }}, {{ identity.state }} {{ identity.zip }}</p>
        </div>
        {% endif %}
      </div>
    </body>
    </html>
    """, identity=None)

@app.route("/generate", methods=["POST"])
def generate_identity():
    theme = request.form.get("theme", "modern")
    location = request.form.get("location", "New York, USA")
    try:
        name = generate_name(theme)
        address = generate_random_address(location)
        identity = {
            "name": name,
            **address
        }
        return render_template_string("""
        <p><a href="/">⬅ Back</a></p>
        <h2>🎭 Generated Identity</h2>
        <p><b>Name:</b> {{ identity.name }}</p>
        <p><b>Street Address:</b> {{ identity.street }}</p>
        <p><b>City, State, ZIP:</b> {{ identity.city }}, {{ identity.state }} {{ identity.zip }}</p>
        """, identity=identity)
    except Exception as e:
        return render_template_string(f"<p>Error: {e}</p><p><a href='/'>Try again</a></p>"), 500

@app.route("/api", methods=["GET"])
def api_identity():
    theme = request.args.get("theme", "modern")
    location = request.args.get("location", "New York, USA")
    try:
        name = generate_name(theme)
        address = generate_random_address(location)
        return jsonify({
            "name": name,
            **address
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------------------

if __name__ == "__main__":
    port = get_free_port()
    print(f"🧙 Identity Conjurer starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
