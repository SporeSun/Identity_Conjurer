from flask import Flask, request, jsonify, render_template_string
import requests, random, json, os, socket

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
app = Flask(__name__)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL  = "https://overpass-api.de/api/interpreter"
HEADERS       = {"User-Agent": "IdentityConjurer/2.0 (contact@example.com)"}
CACHE_FILE    = "cache.json"

# ---------------------------------------------------
# UTILITIES
# ---------------------------------------------------
def get_free_port(start=5000, end=5100):
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise OSError(f"No free ports between {start}-{end}")

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

# ---------------------------------------------------
# NAME GENERATOR
# ---------------------------------------------------
FIRST_NAMES = {
    "modern":  ["Emma","Liam","Olivia","Noah","Sophia","Mason","Ava","Ethan","Isabella","Lucas"],
    "fantasy": ["Elora","Thrain","Mirael","Gorath","Elandra","Fenric","Kael","Seraphine","Tovin","Lira"],
    "sci-fi":  ["Nova","Zyra","Orion","Kaon","Vex","Astra","Rho","Nyx","Ceres","Dray"],
    "silly":   ["Pickle","Snorf","Bloop","Wumbo","Tater","Flibber","Muffin","Doodle","Crumpet","Bonk"]
}
LAST_NAMES = {
    "modern":  ["Johnson","Smith","Brown","Garcia","Martinez","Lee","Davis","Clark","Miller","Taylor"],
    "fantasy": ["Stormforge","Moonshadow","Ironfist","Silverleaf","Windwalker","Bloodfang","Starwhisper","Dawnspire"],
    "sci-fi":  ["Prime","NovaCore","Sigma","Void","Axis","Ion","Nebula","Chrome","Pulse"],
    "silly":   ["McNoodle","Bumblefluff","Wigglesworth","Cheesebottom","Snickerdoodle","Boopington","Flapjack"]
}

def generate_name(theme="modern"):
    if theme not in FIRST_NAMES:
        theme = "modern"
    first = random.choice(FIRST_NAMES[theme])
    last  = random.choice(LAST_NAMES[theme])
    return f"{first} {last}"

# ---------------------------------------------------
# ADDRESS GENERATOR – REAL EXISTING ADDRESSES
# ---------------------------------------------------
def generate_real_address(location_input):
    """Fetch a real existing address (with housenumber) from OSM."""
    params = {"q": location_input, "format": "json", "limit": 1, "polygon_geojson": 1}
    response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError("Location not found.")
    meta = data[0]
    bbox = [float(x) for x in meta["boundingbox"]]
    south, north, west, east = bbox

    # Overpass query for actual building-level addresses
    query = f"""
    [out:json][timeout:30];
    (
      node["addr:housenumber"]["addr:street"]({south},{west},{north},{east});
    );
    out tags center;
    """
    r = requests.post(OVERPASS_URL, data=query, headers=HEADERS)
    r.raise_for_status()
    elements = r.json().get("elements", [])
    valid = [e for e in elements if "addr:street" in e["tags"] and "addr:housenumber" in e["tags"]]

    if not valid:
        raise ValueError("No real addresses found in this area (OSM coverage may be incomplete).")

    item = random.choice(valid)
    tags = item["tags"]
    lat, lon = item.get("lat") or item["center"]["lat"], item.get("lon") or item["center"]["lon"]

    # Reverse lookup for structured address
    rev = requests.get(
        "https://nominatim.openstreetmap.org/reverse",
        params={"lat": lat, "lon": lon, "format": "json"},
        headers=HEADERS
    )
    rev.raise_for_status()
    rev_data = rev.json()
    addr = rev_data.get("address", {})

    city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("hamlet") or "Unknown City"
    state = addr.get("state", "Unknown State")
    zip_code = addr.get("postcode", "00000")

    return {
        "street": f"{tags.get('addr:housenumber')} {tags.get('addr:street')}",
        "city": city,
        "state": state,
        "zip": zip_code
    }

# ---------------------------------------------------
# FLASK ROUTES
# ---------------------------------------------------
@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Identity Conjurer</title>
      <style>
        body { font-family:'Segoe UI',sans-serif; background:linear-gradient(120deg,#7F7FD5,#86A8E7,#91EAE4); margin:0; color:#333; }
        h1 { text-align:center; color:white; padding-top:30px; text-shadow:1px 1px 3px rgba(0,0,0,0.3); }
        .container { width:420px; margin:40px auto; background:#fff; padding:20px; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.1); }
        select,input,button { width:100%; padding:10px; margin-top:10px; border-radius:8px; border:1px solid #ccc; font-size:1em; }
        button { background:#7F7FD5; color:white; font-weight:bold; border:none; cursor:pointer; transition:0.3s; }
        button:hover { background:#6C6CCF; }
        .result { margin-top:20px; text-align:center; font-weight:bold; }
        .label { font-size:0.9em; color:#666; }
      </style>
    </head>
    <body>
      <h1>🧙 Identity Conjurer</h1>
      <div class="container">
        <form method="post" action="/generate">
          <label>Name Style:</label>
          <select name="theme">
            <option value="modern">Modern</option>
            <option value="fantasy">Fantasy</option>
            <option value="sci-fi">Sci-Fi</option>
            <option value="silly">Silly</option>
          </select>
          <label>Location (ZIP or City/State/Country):</label>
          <input name="location" placeholder="e.g. 92675 or Paris, France" required>
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
    theme = request.form.get("theme","modern")
    location = request.form.get("location","New York, USA")
    try:
        name = generate_name(theme)
        address = generate_real_address(location)
        identity = {"name": name, **address}
        return render_template_string("""
        <p><a href="/">⬅ Back</a></p>
        <h2>🎭 Generated Identity</h2>
        <p><b>Name:</b> {{ identity.name }}</p>
        <p><b>Street Address:</b> {{ identity.street }}</p>
        <p><b>City, State, ZIP:</b> {{ identity.city }}, {{ identity.state }} {{ identity.zip }}</p>
        <form action="/" method="get"><button>Generate Another</button></form>
        """, identity=identity)
    except Exception as e:
        return render_template_string(f"<p>Error: {e}</p><p><a href='/'>Try again</a></p>"), 500

@app.route("/api")
def api_identity():
    theme = request.args.get("theme","modern")
    location = request.args.get("location","New York, USA")
    try:
        name = generate_name(theme)
        address = generate_real_address(location)
        return jsonify({"name": name, **address})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
if __name__ == "__main__":
    port = get_free_port()
    print(f"🧙 Identity Conjurer running on port {port} ...")
    app.run(host="0.0.0.0", port=port, debug=True)
