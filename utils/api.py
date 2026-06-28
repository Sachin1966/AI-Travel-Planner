import requests
import json
import random
from utils.mock_data import MOCK_ITINERARIES

# User agent for Nominatim geocoding (OpenStreetMap) to prevent blockages
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def geocode_destination(destination_name):
    """
    Geocodes a destination name to (latitude, longitude) using OpenStreetMap Nominatim.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(destination_name)}&format=json&limit=1"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

def fetch_weather(lat, lon):
    """
    Fetches real-time weather and a 3-day forecast from Open-Meteo API.
    """
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&timezone=auto"
        )
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            current = data.get("current_weather", {})
            daily = data.get("daily", {})
            
            # Map weather codes to emojis / readable names
            weather_codes = {
                0: ("Sunny", "☀️"),
                1: ("Mainly Clear", "🌤️"), 2: ("Partly Cloudy", "⛅"), 3: ("Overcast", "☁️"),
                45: ("Foggy", "🌫️"), 48: ("Depositing Rime Fog", "🌫️"),
                51: ("Light Drizzle", "🌦️"), 53: ("Moderate Drizzle", "🌦️"), 55: ("Dense Drizzle", "🌦️"),
                61: ("Slight Rain", "🌧️"), 63: ("Moderate Rain", "🌧️"), 65: ("Heavy Rain", "🌧️"),
                71: ("Slight Snow", "🌨️"), 73: ("Moderate Snow", "🌨️"), 75: ("Heavy Snow", "🌨️"),
                80: ("Slight Rain Showers", "🌦️"), 81: ("Moderate Rain Showers", "🌦️"), 82: ("Violent Rain Showers", "🌧️"),
                95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm with Hail", "⛈️")
            }
            code = current.get("weathercode", 0)
            desc, emoji = weather_codes.get(code, ("Unknown", "🌡️"))
            
            # Format forecast
            forecast = []
            if daily:
                for i in range(min(3, len(daily.get("time", [])))):
                    forecast.append({
                        "date": daily["time"][i],
                        "max_temp": daily["temperature_2m_max"][i],
                        "min_temp": daily["temperature_2m_min"][i],
                        "precip_prob": daily["precipitation_probability_max"][i]
                    })
                    
            return {
                "temp": current.get("temperature"),
                "wind_speed": current.get("windspeed"),
                "description": desc,
                "emoji": emoji,
                "forecast": forecast
            }
    except Exception as e:
        print(f"Weather fetch error: {e}")
    return None

def fetch_ollama_models(base_url="http://localhost:11434"):
    """
    Fetches the list of available local models from the Ollama instance.
    """
    try:
        res = requests.get(f"{base_url}/api/tags", timeout=5)
        if res.status_code == 200:
            data = res.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
    except Exception as e:
        print(f"Ollama connection error: {e}")
    return []

def _get_system_prompt(details):
    """
    Generates a detailed system prompt with JSON schema constraints.
    """
    interests_str = ", ".join(details['interests']) if details['interests'] else "General Sightseeing"
    custom_request_str = f"Special Custom Requirements: {details['custom_prompt']}" if details['custom_prompt'] else ""
    
    return f"""You are an elite, AI-powered travel assistant. Generate a highly detailed, professional, and exciting travel itinerary based on the following criteria:
- Destination: {details['destination']}
- Duration: {details['duration']} Days
- Budget Level: {details['budget']}
- Travel Party: {details['party']}
- Areas of Interest: {interests_str}
{custom_request_str}

IMPORTANT RULES:
1. Provide a beautiful itinerary with exactly 3 activities per day (Morning, Afternoon, Evening) for a total of {details['duration']} days.
2. Approximate real-world latitude (lat) and longitude (lng) coordinates for each activity. Place markers reasonably close to the destination center (within 10-20km).
3. The response MUST be a single raw JSON object that strictly adheres to the schema below.
4. Do NOT wrap the JSON in markdown code blocks like ```json or ```. Return only the raw JSON.
5. All costs should be estimates in local currency or USD (e.g., "$15", "Free", "$120").
6. Provide lodging suggestions matching the budget level (Luxury, Mid-range, Budget).
7. Suggest authentic local dishes/beverages to try.

JSON Schema:
{{
  "destination": "Name of the destination",
  "description": "A compelling 2-sentence summary of what makes this destination amazing for this traveler.",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "total_budget_est": "Estimated total trip cost range (e.g. '$1,200 - $2,000')",
  "budget_breakdown": {{
    "Accommodations": 40,
    "Food & Drinks": 30,
    "Activities": 20,
    "Transport": 10
  }},
  "itinerary": [
    {{
      "day": 1,
      "theme": "Theme of Day 1",
      "activities": [
        {{
          "time": "Morning",
          "name": "Activity Name",
          "description": "Engaging description of what to do, where to eat, or what to see.",
          "lat": 48.8530,
          "lng": 2.3499,
          "cost": "$15",
          "duration": "2 hours"
        }}
      ]
    }}
  ],
  "accommodations": [
    {{
      "name": "Suggested Hotel Name",
      "type": "Luxury / Mid-range / Budget",
      "price_level": "$$$$ / $$$ / $$ / $",
      "description": "Short description of why this is a great choice."
    }}
  ],
  "local_flavors": {{
    "cuisines": [
      {{"name": "Dish Name", "description": "Short appetizing description"}}
    ],
    "beverages": [
      {{"name": "Beverage Name", "description": "Short appetizing description"}}
    ],
    "hotspots": "Recommended neighborhoods or areas for street food, dining, and cafes"
  }}
}}
"""

def generate_itinerary(provider, config, details):
    """
    Orchestrates the generation of the itinerary using the chosen provider.
    """
    destination_clean = details["destination"].strip().lower()
    
    # 1. Handle Mock/Demo Provider
    if provider == "Mock/Demo":
        # Search for a match in mock keys
        for key in MOCK_ITINERARIES:
            if key in destination_clean:
                # Return deep copy of the mock itinerary
                itinerary_data = json.loads(json.dumps(MOCK_ITINERARIES[key]))
                # Adjust duration if requested duration is less than mock duration
                req_days = details["duration"]
                if len(itinerary_data["itinerary"]) > req_days:
                    itinerary_data["itinerary"] = itinerary_data["itinerary"][:req_days]
                return itinerary_data
        
        # If no mock data found, fallback to dynamic mock generation to avoid errors
        return _generate_heuristic_fallback(details)

    system_prompt = _get_system_prompt(details)
    raw_response = ""
    
    # Geocode destination first to get a center point in case AI coordinate generation fails
    center_lat, center_lon = geocode_destination(details["destination"])
    if not center_lat:
        center_lat, center_lon = 48.8566, 2.3522  # Default to Paris center if geocoding fails

    # 2. Handle Ollama Provider
    if provider == "Ollama":
        base_url = config.get("ollama_url", "http://localhost:11434")
        model = config.get("ollama_model")
        if not model:
            raise ValueError("No Ollama model selected. Please select a model in settings.")
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a travel itinerary generator that outputs only strict JSON."},
                {"role": "user", "content": system_prompt}
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        
        try:
            res = requests.post(f"{base_url}/api/chat", json=payload, timeout=90)
            if res.status_code == 200:
                result_json = res.json()
                raw_response = result_json.get("message", {}).get("content", "")
            else:
                raise Exception(f"Ollama server returned error code {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Failed to connect to local Ollama instance: {str(e)}")

    # 3. Handle Gemini Provider
    elif provider == "Gemini API":
        api_key = config.get("gemini_key")
        if not api_key:
            raise ValueError("Gemini API Key is missing. Please add your key in the settings.")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": system_prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7
            }
        }
        
        try:
            res = requests.post(url, json=payload, timeout=60)
            if res.status_code == 200:
                result_json = res.json()
                candidates = result_json.get("candidates", [])
                if candidates:
                    raw_response = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                else:
                    raise Exception("Gemini returned empty candidates. Check API usage limits.")
            else:
                raise Exception(f"Gemini API returned error code {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Gemini API generation failed: {str(e)}")

    # Parse and clean the response
    if not raw_response:
        raise Exception("AI model returned an empty response. Please try again.")

    # Clean markdown code blocks if any (e.g. ```json ... ```)
    cleaned_res = raw_response.strip()
    if cleaned_res.startswith("```"):
        # Strip leading ```json or ```
        cleaned_res = cleaned_res.split("\n", 1)[1] if "\n" in cleaned_res else cleaned_res
        if cleaned_res.endswith("```"):
            cleaned_res = cleaned_res[:-3]
    cleaned_res = cleaned_res.strip()

    try:
        itinerary_data = json.loads(cleaned_res)
    except json.JSONDecodeError as e:
        # Fallback to display raw output in logs and try a soft regex clean
        print(f"Failed to parse JSON. Error: {e}. Raw response snippet: {raw_response[:200]}")
        raise Exception("The AI model response could not be parsed as JSON. Please try again or switch models.")

    # Ensure latitude and longitude are set and valid
    if "latitude" not in itinerary_data or not itinerary_data["latitude"]:
        itinerary_data["latitude"] = center_lat
    if "longitude" not in itinerary_data or not itinerary_data["longitude"]:
        itinerary_data["longitude"] = center_lon

    # Sanitize itinerary activities and inject fallback coordinates if they are missing or invalid
    for d_idx, day_plan in enumerate(itinerary_data.get("itinerary", [])):
        for a_idx, act in enumerate(day_plan.get("activities", [])):
            # Fallback coordinates: centered near destination with a small random jitter
            if "lat" not in act or not act["lat"] or "lng" not in act or not act["lng"]:
                offset_lat = (random.random() - 0.5) * 0.04
                offset_lng = (random.random() - 0.5) * 0.04
                act["lat"] = itinerary_data["latitude"] + offset_lat
                act["lng"] = itinerary_data["longitude"] + offset_lng
            else:
                try:
                    act["lat"] = float(act["lat"])
                    act["lng"] = float(act["lng"])
                except:
                    offset_lat = (random.random() - 0.5) * 0.04
                    offset_lng = (random.random() - 0.5) * 0.04
                    act["lat"] = itinerary_data["latitude"] + offset_lat
                    act["lng"] = itinerary_data["longitude"] + offset_lng

    return itinerary_data

def _generate_heuristic_fallback(details):
    """
    Generates a realistic mock fallback itinerary dynamically for any location
    to ensure the app behaves elegantly even in offline/demo mode for non-mocked cities.
    """
    dest = details["destination"]
    dur = details["duration"]
    budget = details["budget"]
    interests = details["interests"] if details["interests"] else ["Sightseeing"]
    party = details["party"]
    
    # Geocode to center map
    lat, lon = geocode_destination(dest)
    if not lat:
        lat, lon = 34.0522, -118.2437  # Default to Los Angeles center
        
    activities_pool = {
        "Adventure": [
            ("Zip-lining and Canopy Tour", "Thrill-seeking zip-line flights across forest canopy."),
            ("Mountain Bike Trail Expedition", "Adrenaline-filled downhill riding through rugged terrain."),
            ("Rock Climbing & Bouldering", "Scale scenic cliffs with experienced local guides."),
            ("Kayaking or Paddleboarding", "Paddle through beautiful local waterways or bays.")
        ],
        "Culture": [
            ("Historic Museum Guided Tour", "Explore local heritage, archaeology, and historical artifacts."),
            ("Old Town Walking Exploration", "Admire historic architecture and learn neighborhood legends."),
            ("Traditional Art/Craft Workshop", "Participate in a hands-on crafting class taught by local artisans."),
            ("Ancient Palace/Temple Visit", "Wander through centuries-old religious or royal buildings.")
        ],
        "Food": [
            ("Gourmet Food Tasting Tour", "Sample signature appetizers and street foods from family-run stalls."),
            ("Local Market Culinary Safari", "Browse colorful stalls filled with regional spices and fresh produce."),
            ("Fine Dining & Wine Pairing", "A multi-course dinner highlighting regional wines and modern cuisines."),
            ("Cooking Masterclass", "Learn the secrets of preparing authentic local specialties.")
        ],
        "Nature": [
            ("Scenic Botanical Gardens Walk", "Stroll past manicured flowerbeds, greenhouses, and exotic flora."),
            ("Sunset Ridge Hike", "Hike up to a panorama point to view the sunset over the valley."),
            ("Wildlife Sanctuary Visit", "Spot native animals, birds, and conservation projects."),
            ("National Park Scenic Drive", "Stop at iconic viewpoints and waterfall lookouts.")
        ],
        "Relaxation": [
            ("Thermal Spa & Massage Experience", "Soak in mineral hot springs followed by a signature massage."),
            ("Leisurely Beach Picnic", "Unwind on sandy shores with delicious snacks and relaxing waves."),
            ("Scenic Harbor Cruise", "Feel the breeze on a catamaran while listening to acoustic music."),
            ("Quiet Café Reading Afternoon", "Sip artisanal drinks in a serene courtyard garden.")
        ],
        "Shopping": [
            ("Local Artisan Craft Bazaar", "Shop for hand-woven textiles, ceramics, and custom jewelry."),
            ("High-End Fashion Avenue Stroll", "Browse flagship boutiques and designer studios."),
            ("Flea Market Antique Hunting", "Sift through vintage collectibles, books, and quirky items."),
            ("Modern Shopping Mall & Arcade", "Experience multi-story malls with digital entertainment centers.")
        ],
        "Family": [
            ("Interactive Science Center", "Engaging, hands-on science exhibits fun for all ages."),
            ("Local Zoo or Aquarium Visit", "Get up close to penguins, sharks, and exotic mammals."),
            ("Adventure Theme Park Trip", "Spend the day riding rollercoasters and enjoying themed shows."),
            ("Scenic Parks & Playgrounds", "Let the kids run free in clean green spaces with fun amenities.")
        ]
    }
    
    # Fallback pool
    general_pool = [
        ("Central Plaza Walk", "Explore the historic town square and take photos near the central monument."),
        ("Scenic Viewpoint Drive", "Head to the highest point in town for a view of the landscape."),
        ("Local Bistro Dinner", "Indulge in a cozy meal of regional comforts in a popular neighborhood.")
    ]
    
    itinerary = []
    for day_num in range(1, dur + 1):
        day_interests = interests.copy()
        random.shuffle(day_interests)
        
        day_acts = []
        times = ["Morning", "Afternoon", "Evening"]
        
        for time_slot in times:
            # Pick activity category based on interests
            cat = day_interests.pop() if day_interests else random.choice(list(activities_pool.keys()))
            pool = activities_pool.get(cat, general_pool)
            act_choice = random.choice(pool)
            
            # Jitter coordinates slightly around center
            act_lat = lat + (random.random() - 0.5) * 0.06
            act_lng = lon + (random.random() - 0.5) * 0.06
            
            day_acts.append({
                "time": time_slot,
                "name": f"{act_choice[0]} (Theme: {cat})",
                "description": f"{act_choice[1]} This activity is tailored for {party} seeking a {budget.lower()} budget experience.",
                "lat": act_lat,
                "lng": act_lng,
                "cost": "Free" if budget == "Budget" else (f"${random.randint(10, 30)}" if budget == "Mid-range" else f"${random.randint(50, 150)}"),
                "duration": "2-3 hours"
            })
            
        itinerary.append({
            "day": day_num,
            "theme": f"Exploring local {interests[0] if interests else 'Culture'}",
            "activities": day_acts
        })
        
    return {
        "destination": f"{dest} (Heuristic Demo)",
        "description": f"A delightful exploration of {dest} custom-curated for {party.lower()} travelers. Your itinerary highlights local interests in {', '.join(interests)}.",
        "latitude": lat,
        "longitude": lon,
        "total_budget_est": "$500 - $900" if budget == "Budget" else ("$1,200 - $2,200" if budget == "Mid-range" else "$3,500 - $6,000"),
        "budget_breakdown": {
            "Accommodations": 45,
            "Food & Drinks": 30,
            "Activities": 15,
            "Transport": 10
        },
        "itinerary": itinerary,
        "accommodations": [
            {
                "name": f"The Grand {dest.split(',')[0]} Hotel",
                "type": "Luxury",
                "price_level": "$$$$",
                "description": "Exquisite luxury hotel offering world-class services and spa facilities."
            },
            {
                "name": f"{dest.split(',')[0]} Comfort Inn",
                "type": "Mid-range",
                "price_level": "$$",
                "description": "Comfortable, clean rooms located close to transport links and bistros."
            },
            {
                "name": f"Central Backpackers {dest.split(',')[0]}",
                "type": "Budget",
                "price_level": "$",
                "description": "Affordable dorms and private rooms with an active social lounge and free breakfast."
            }
        ],
        "local_flavors": {
            "cuisines": [
                {"name": f"Signature Regional Platter", "description": "A delightful plate featuring the best regional cheeses, slow-cooked meats, and local vegetables."},
                {"name": "Traditional Savory pastry", "description": "Freshly baked pie filled with spiced local herbs and slow-roasted beef."}
            ],
            "beverages": [
                {"name": "Regional Brew", "description": "A popular local craft beverage brewed with local mountain spring water."},
                {"name": "Spiced Herbal Tea", "description": "Warm, comforting tea infused with native wildflower honey and cinnamon."}
            ],
            "hotspots": "The Old Market Street and River Walk district for the best local cafes, bakeries, and food stalls."
        }
    }
