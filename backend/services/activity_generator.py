import os
import json
import requests
import random
from dotenv import load_dotenv
from utils.helpers import geocode_destination, get_destination_currency

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def regenerate_single_activity(
    destination: str,
    day_num: int,
    time_slot: str,
    style: str,
    budget: str,
    custom_instruction: str,
    current_activity: dict
) -> dict:
    """
    Asks Ollama to regenerate a specific activity slot (Morning, Afternoon, Evening)
    based on custom instruction, keeping destination, style, and budget constraints.
    Falls back to a heuristic replacement if Ollama is offline or fails.
    """
    
    # Resolve destination coordinates for default fallbacks
    lat, lon = geocode_destination(destination)
    if not lat:
        lat, lon = 48.8566, 2.3522 # Paris fallback
        
    # Resolve local currency
    currency_symbol, currency_code = get_destination_currency(destination)
        
    system_instruction = f"""You are an elite travel planner AI. Regenerate a single activity for a trip.
You are replacing the CURRENT activity with a NEW activity based on the USER INSTRUCTION.

TRIP CONTEXT:
- Destination: {destination}
- Day Number: {day_num}
- Time Slot: {time_slot}
- Travel Style: {style}
- Budget Tier: {budget}

CURRENT ACTIVITY TO BE REPLACED:
- Name: {current_activity.get('name', 'N/A')}
- Description: {current_activity.get('description', 'N/A')}
- Cost: {current_activity.get('cost', 'N/A')}
- Duration: {current_activity.get('duration', 'N/A')}

USER OVERRIDE INSTRUCTION (Follow this strictly):
"{custom_instruction}"

HTML/Legibility Rule:
- All text should be clear and plain.

OUTPUT RULES:
1. You must output exactly one JSON object representing the replacement activity.
2. The response MUST be a single raw JSON object that strictly adheres to the schema below.
3. Set coordinates (lat, lng) representing a valid spot in {destination}.
4. Do NOT include markdown code blocks like ```json. Output only raw JSON.
5. The cost estimate MUST be specified in the local currency of the destination, which is {currency_symbol} ({currency_code}).
   For example, use '{currency_symbol}X' where X is the value (e.g. '{currency_symbol}20' or '{currency_symbol}150').

JSON Schema:
{{
  "time": "{time_slot}",
  "name": "New Activity/Attraction Name",
  "description": "Engaging description explaining what to see/do, keeping user instruction in mind.",
  "lat": {lat},
  "lng": {lon},
  "cost": "Cost estimate (e.g. Free or {currency_symbol}20)",
  "duration": "Duration (e.g. 2 hours)"
}}
"""

    raw_response = ""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": "You are a travel database planner that outputs strict JSON."},
                {"role": "user", "content": system_instruction}
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        res = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=45)
        if res.status_code == 200:
            result_json = res.json()
            raw_response = result_json.get("message", {}).get("content", "")
    except Exception as e:
        print(f"Ollama failed to regenerate activity: {e}. Using fallback generator.")

    if raw_response:
        try:
            cleaned_res = raw_response.strip()
            if cleaned_res.startswith("```"):
                cleaned_res = cleaned_res.split("\n", 1)[1] if "\n" in cleaned_res else cleaned_res
                if cleaned_res.endswith("```"):
                    cleaned_res = cleaned_res[:-3]
            cleaned_res = cleaned_res.strip()
            
            activity_data = json.loads(cleaned_res)
            
            # Ensure coordinates and slot time exist
            activity_data["time"] = time_slot
            if "lat" not in activity_data or not activity_data["lat"] or "lng" not in activity_data or not activity_data["lng"]:
                activity_data["lat"] = lat + (random.random() - 0.5) * 0.04
                activity_data["lng"] = lon + (random.random() - 0.5) * 0.04
                
            return activity_data
        except Exception as parse_err:
            print(f"Failed to parse activity JSON: {parse_err}. Falling back.")
            
    # Heuristic Local Fallback
    fallback_names = {
        "Morning": [f"Guided Tour of {destination} Historic Quarter", "Local Market Exploration & Breakfast"],
        "Afternoon": ["Scenic Viewpoint Walk & Cafe Tasting", "Art Gallery Visit & Shopping"],
        "Evening": ["Fine Culinary Dinner Experience", "Sunset Cruise & Walk along the River/Beach"]
    }
    
    name = random.choice(fallback_names.get(time_slot, ["Custom Local Activity"]))
    desc = f"Enjoy a customized {time_slot.lower()} activity matching your interest: '{custom_instruction}'. We recommend exploring central spots in {destination}."
    cost = "Free" if budget == "Budget" else (f"{currency_symbol}{random.randint(10, 30)}" if budget == "Mid-range" else f"{currency_symbol}{random.randint(50, 120)}")
    
    return {
        "time": time_slot,
        "name": name,
        "description": desc,
        "lat": lat + (random.random() - 0.5) * 0.03,
        "lng": lon + (random.random() - 0.5) * 0.03,
        "cost": cost,
        "duration": "2 hours"
    }
