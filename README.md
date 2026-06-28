# Expedition AI - Production-Ready AI Travel Planner

Expedition AI is a decoupled, production-ready AI-Powered Travel Planner that designs highly personalized daily travel itineraries. Users can specify their destination, duration (1–10 days), budget level, total budget amount, travel party size, travel style, and interests to instantly generate comprehensive, geolocated travel plans.

The architecture is built with a clean separation of concerns, featuring:
1. **Frontend Dashboard (Streamlit)**: A sleek, dark glassmorphic user interface showing timetabled activity timelines, local culinary specialties, current weather conditions, lodging options, calendar syncs, PDF downloads, and a conversational travel assistant chatbot.
2. **Backend Engine (FastAPI)**: REST APIs that orchestrate external travel services, run budget converters, geocode destinations, generate structured travel plans, and handle calendar / PDF exports.
3. **Database (SQLite + SQLAlchemy ORM)**: A light relational database that persists generated trips and chat histories.
4. **AI Core (Ollama)**: Connects to local LLMs (like `llama3` or `mistral`) to compile structured itineraries using strict JSON schemas and run chat interactions.

---

## 🔌 API Integrations & Purposes

Expedition AI integrates several industry-standard and public APIs to build a cohesive travel planner. If any private API keys are omitted in `.env`, the system automatically falls back to geocoded Nominatim/OSRM data combined with localized mock templates to ensure uninterrupted, high-quality output.

| API Name | Endpoint / Resource | Purpose | Usage in Project |
| :--- | :--- | :--- | :--- |
| **OpenStreetMap Nominatim** | `https://nominatim.openstreetmap.org` | Geocoding & Address Resolution | Resolves user-entered text (e.g. "Paris" or "Coimbatore") into exact latitude/longitude coordinates and country codes, enabling local currency lookups and mapping. |
| **OpenStreetMap Nominatim (Discovery)** | `https://nominatim.openstreetmap.org/search` | Dynamic Hotel & Attraction Fetching | Queries osm search lists dynamically for `"hotels in {city}"` and `"tourist attractions in {city}"` to fetch real, local venues and landmarks for 100+ cities globally when private keys are missing. |
| **OSRM (Open Source Routing Machine)** | `http://router.project-osrm.org/route/v1/driving/` | Roadway Driving Routes | Fetches coordinate paths matching actual road networks instead of straight lines. Renders color-coded, day-by-day street routes directly on the Folium map. |
| **Amadeus Travel API** | `https://test.api.amadeus.com/v1` | Lodging Search | Queries 3/4/5-star hotels near the resolved coordinates of the destination, filtered by the user's budget tier. |
| **Google Places API** | `https://maps.googleapis.com/maps/api/place` | Points of Interest Search | Discovers highly-rated local landmarks, parks, and sights matching user interests, providing ratings, reviews, and coordinates. |
| **OpenWeatherMap API / Open-Meteo** | `https://api.openweathermap.org` | Weather Reports & packing advice | Fetches real-time temperature, wind speed, and weather descriptions (accompanied by custom emojis) alongside tailored packing recommendations. |
| **Ollama Local LLM API** | `http://localhost:11434/api/chat` | AI Itinerary Compilation & Chat | Feeds structured context (hotels, landmarks, weather, and budget details) to a local LLM to return a formatted itinerary conforming to a strict JSON schema, and powers the conversational sidebar assistant. |

---

## 🛠️ Technical Stack
* **Web UI**: Streamlit + HTML5 + Custom Glassmorphism CSS
* **API Service**: FastAPI + Uvicorn
* **Database**: SQLite + SQLAlchemy ORM
* **Local LLM**: Ollama (recommended: `llama3`, `llama3:8b`, or `mistral`)
* **Interactive Maps**: Folium + Streamlit-Folium wrapper
* **Export Engines**: ReportLab (PDF compilation) + standard iCalendar `text/calendar` (.ics) format

---

## 📂 Project Structure
```text
travel_planner/
├── app.py                      # Streamlit Frontend Dashboard & Chat UI
├── requirements.txt            # Python Dependencies
├── .env                        # Local Environment Configuration
├── travel_planner.db           # Relational SQLite Database (auto-generated)
├── database/
│   ├── db.py                   # SQLAlchemy Engine, Session, & DB Init
│   └── models.py               # ORM Models (Trip, ChatMessage)
├── backend/
│   ├── api.py                  # FastAPI Endpoint Routes (/generate-itinerary, /chat, etc.)
│   └── services/
│       ├── weather_service.py  # Weather queries & packing recommendations
│       ├── hotel_service.py    # Amadeus lookup & dynamic geocoded OSM fallbacks
│       ├── attraction_service.py# Google Places & dynamic geocoded OSM fallbacks
│       ├── budget_service.py   # Multi-category allocation splitter & savings analyzer
│       ├── activity_generator.py# Single activity slot regeneration engine
│       └── itinerary_generator.py# Ollama prompter & localized fallback engine
├── utils/
│   ├── helpers.py              # Geocoder, country-level currency detector, & Nominatim cache
│   ├── map_generator.py        # OSRM roadway calculator & Folium rendering engine
│   └── pdf_generator.py        # ReportLab PDF exporter
```

---

## 💾 Relational Database Schema

The database (`travel_planner.db`) is automatically initialized and upgraded on FastAPI startup.

### 1. `trips` Table
Stores generated itineraries, lodging, weather, and local flavors.
* `id` (INTEGER, Primary Key): Unique ID of the trip.
* `destination` (VARCHAR): Resolved destination city name.
* `duration` (INTEGER): Trip length in days.
* `budget` (VARCHAR): User budget level ("Budget", "Mid-range", "Luxury").
* `travelers` (INTEGER): Number of travelers.
* `style` (VARCHAR): Selected travel style.
* `interests` (VARCHAR): Comma-separated list of interests.
* `total_budget_est` (VARCHAR): Formatted budget value (automatically parsed and converted to local currency, e.g. `₹25,000` or `€350`).
* `budget_breakdown_json` (TEXT): JSON percentages for lodging, food, transport, activities, and misc.
* `weather_json` (TEXT): Serialized temperature, wind, and packing advice dictionary.
* `itinerary_json` (TEXT): Array of daily plans containing structured morning, afternoon, and evening slots with coordinates.
* `accommodations_json` (TEXT): Array of suggested hotels with name, price tier, and exact coordinates.
* `local_flavors_json` (TEXT): Famous local cuisines, drinks, and dining hotspots.
* `created_at` (DATETIME): Generation timestamp.

### 2. `chat_messages` Table
Maintains context history for the sidebar Chat Assistant.
* `id` (INTEGER, Primary Key): Message ID.
* `trip_id` (INTEGER, Foreign Key to `trips.id`): Active trip ID reference.
* `role` (VARCHAR): Actor role ("user" or "assistant").
* `content` (TEXT): Plaintext message content.
* `timestamp` (DATETIME): Timestamp.

---

## 🚀 Setup & Execution

### 1. Prerequisites
* **Python 3.10+** installed.
* **Ollama** installed locally.
  * Download and run Ollama from [ollama.com](https://ollama.com).
  * Pull your preferred model (e.g. `llama3`):
    ```bash
    ollama pull llama3
    ```
  * Verify Ollama is running in your task tray or run:
    ```bash
    ollama serve
    ```

### 2. Installation & Configuration
1. Clone or download this project workspace.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environmental variables by creating a `.env` file in the root directory:
   ```text
   DATABASE_URL=sqlite:///./travel_planner.db
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   
   # Optional private keys. Leave blank to run automatically on geocoded OSM fallbacks:
   OPENWEATHER_API_KEY=
   GOOGLE_PLACES_API_KEY=
   AMADEUS_CLIENT_ID=
   AMADEUS_CLIENT_SECRET=
   ```

### 3. Running the Project
Start the servers in two separate terminals:

* **Terminal 1: Start FastAPI Backend**
  ```bash
  uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
  ```
  * Swagger interactive docs will be available at `http://127.0.0.1:8000/docs`.

* **Terminal 2: Start Streamlit Frontend**
  ```bash
  streamlit run app.py
  ```
  * Open the app in your browser at `http://localhost:8501`.

---

## ☁️ Deployment Guidelines (Streamlit Cloud)
1. Push the code repository to GitHub (ensure `travel_planner.db` is ignored in `.gitignore`).
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io).
3. Connect your repository, choose the branch, and set `app.py` as the entrypoint.
4. Under **Advanced settings**, set up your environment variables. 
   * *Note*: If deploying to a public server without local Ollama access, set the model parameters to connect to a hosted API or enjoy the robust geocoded local fallbacks. The system is designed to seamlessly run fallback schedules and mock guides if Ollama is unreachable.
