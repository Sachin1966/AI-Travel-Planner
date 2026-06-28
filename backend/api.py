from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import requests
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Database Imports
from database.db import get_db, init_db
from database.models import Trip, ChatMessage

# Backend Services Imports
from backend.services.weather_service import fetch_weather_report
from backend.services.hotel_service import fetch_hotels
from backend.services.attraction_service import fetch_attractions
from backend.services.budget_service import analyze_budget
from backend.services.itinerary_generator import generate_full_itinerary
from backend.services.activity_generator import regenerate_single_activity

# Utilities Imports
from utils.helpers import geocode_destination, get_destination_currency, parse_currency_amount, convert_currency
from utils.pdf_generator import generate_pdf_itinerary

load_dotenv()

app = FastAPI(
    title="AI-Powered Travel Planner API",
    description="Backend services for geocoding, weather forecasts, lodging suggestions, budget analysis, structured itineraries, and PDF downloads.",
    version="1.0"
)

# Enable CORS for browser-based client invocations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Initialization on Startup
@app.on_event("startup")
def startup_event():
    init_db()

# --- PYDANTIC MODEL SCHEMAS ---
class ItineraryRequest(BaseModel):
    destination: str
    duration: int
    budget: str         # "Budget", "Mid-range", "Luxury"
    total_budget_val: str # Total value (e.g. "$1500" or "INR 50000")
    travelers: int
    style: str          # "Luxury", "Budget", "Backpacking", "Family", "Adventure"
    interests: List[str]
    custom_prompt: Optional[str] = ""

class ChatRequest(BaseModel):
    trip_id: int
    message: str

class ActivityRegenRequest(BaseModel):
    trip_id: int
    day: int
    time_slot: str
    custom_instruction: str

# --- REST ENDPOINTS ---

@app.post("/generate-itinerary")
def api_generate_itinerary(req: ItineraryRequest, db: Session = Depends(get_db)):
    """
    Triggers all external services, asks Ollama to build a structured itinerary,
    persists the final plan in SQLite database, and returns the Trip record.
    """
    # 1. Geocode Destination
    lat, lon = geocode_destination(req.destination)
    if not lat:
        raise HTTPException(status_code=400, detail=f"Destination '{req.destination}' could not be geocoded. Check spelling.")

    # 1.5 Resolve destination currency and convert user budget
    currency_symbol, currency_code = get_destination_currency(req.destination)
    user_val, user_cc = parse_currency_amount(req.total_budget_val)
    converted_val = convert_currency(user_val, user_cc, currency_code)
    target_budget_val = f"{currency_symbol}{int(converted_val)}"

    # 2. Fetch Weather
    weather = fetch_weather_report(lat, lon)

    # 3. Fetch Hotels
    hotels = fetch_hotels(req.destination, req.budget)

    # 4. Fetch Attractions
    attractions = fetch_attractions(req.destination, req.interests)

    # 5. Analyze Budget
    budget_analysis = analyze_budget(req.budget, target_budget_val, currency_symbol)

    # 6. Generate AI Itinerary via Ollama
    details = {
        "destination": req.destination,
        "duration": req.duration,
        "budget": req.budget,
        "party": f"{req.travelers} Traveler(s)",
        "style": req.style,
        "interests": req.interests,
        "custom_prompt": req.custom_prompt,
        "currency_symbol": currency_symbol,
        "currency_code": currency_code
    }
    
    try:
        full_plan = generate_full_itinerary(details, hotels, attractions, weather, budget_analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    # 7. Write to SQLite Database
    try:
        new_trip = Trip(
            destination=req.destination,
            duration=req.duration,
            budget=req.budget,
            travelers=req.travelers,
            style=req.style,
            interests=",".join(req.interests),
            total_budget_est=full_plan.get("total_budget_est", req.total_budget_val),
            budget_breakdown_json=json.dumps(full_plan.get("budget_breakdown", {})),
            weather_json=json.dumps(full_plan.get("weather", {})),
            itinerary_json=json.dumps(full_plan.get("itinerary", [])),
            accommodations_json=json.dumps(full_plan.get("accommodations", [])),
            local_flavors_json=json.dumps(full_plan.get("local_flavors", {})),
        )
        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)
        
        # Format the response object to return clean deserialized fields
        return {
            "trip_id": new_trip.id,
            "destination": new_trip.destination,
            "duration": new_trip.duration,
            "budget": new_trip.budget,
            "travelers": new_trip.travelers,
            "style": new_trip.style,
            "interests": req.interests,
            "description": full_plan.get("description") or f"A custom {new_trip.duration}-day {new_trip.style.lower()} itinerary to {new_trip.destination} for {new_trip.travelers} traveler(s) featuring {', '.join(req.interests) if req.interests else 'local sights'}.",
            "total_budget_est": new_trip.total_budget_est,
            "budget_breakdown": full_plan.get("budget_breakdown"),
            "weather": full_plan.get("weather"),
            "itinerary": full_plan.get("itinerary"),
            "accommodations": full_plan.get("accommodations"),
            "local_flavors": full_plan.get("local_flavors"),
            "travel_tips": full_plan.get("travel_tips", []),
            "latitude": lat,
            "longitude": lon
        }
    except Exception as db_err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database write failed: {str(db_err)}")

@app.get("/trips")
def api_get_trips(db: Session = Depends(get_db)):
    """
    Returns list of all saved trips in the database.
    """
    trips = db.query(Trip).order_by(Trip.created_at.desc()).all()
    return [
        {
            "trip_id": t.id,
            "destination": t.destination,
            "duration": t.duration,
            "budget": t.budget,
            "travelers": t.travelers,
            "style": t.style,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M")
        } for t in trips
    ]

@app.get("/trip/{trip_id}")
def api_get_trip(trip_id: int, db: Session = Depends(get_db)):
    """
    Retrieves and deserializes a single trip record.
    """
    t = db.query(Trip).filter(Trip.id == trip_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trip record not found.")
        
    lat, lon = geocode_destination(t.destination)
    if not lat:
        lat, lon = 48.8566, 2.3522 # Default fallback
        
    # Reconstruct geocode coordinates in response
    return {
        "trip_id": t.id,
        "destination": t.destination,
        "duration": t.duration,
        "budget": t.budget,
        "travelers": t.travelers,
        "style": t.style,
        "interests": t.interests.split(",") if t.interests else [],
        "description": f"A custom {t.duration}-day {t.style.lower()} itinerary to {t.destination} for {t.travelers} traveler(s) featuring {t.interests.replace(',', ', ') if t.interests else 'local sights'}.",
        "total_budget_est": t.total_budget_est,
        "budget_breakdown": json.loads(t.budget_breakdown_json) if t.budget_breakdown_json else {},
        "weather": json.loads(t.weather_json) if t.weather_json else {},
        "itinerary": json.loads(t.itinerary_json),
        "accommodations": json.loads(t.accommodations_json) if t.accommodations_json else [],
        "local_flavors": json.loads(t.local_flavors_json) if t.local_flavors_json else {},
        "travel_tips": [
            "Keep digital copies of all identification on your phone.",
            "Use local public transit cards to save money.",
            "Pack versatile layers as local weather can shift.",
            "Learn key local phrases to connect with residents."
        ],
        "latitude": lat,
        "longitude": lon
    }

@app.post("/chat")
def api_chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Feeds the itinerary data as context to Ollama along with previous chat logs
    to output specific responses, and saves history.
    """
    t = db.query(Trip).filter(Trip.id == req.trip_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found.")
        
    # Load previous history
    history = db.query(ChatMessage).filter(ChatMessage.trip_id == req.trip_id).order_by(ChatMessage.timestamp.asc()).all()
    
    # Condense accommodations and itinerary to fit fast local prefill context
    try:
        accomm_list = json.loads(t.accommodations_json) if t.accommodations_json else []
        lodging_summary = ", ".join([f"{h.get('name')} ({h.get('type')}, {h.get('approx_price')})" for h in accomm_list])
    except Exception:
        lodging_summary = "N/A"
        
    try:
        itin_list = json.loads(t.itinerary_json) if t.itinerary_json else []
        days_summary = []
        for day in itin_list:
            d_num = day.get("day", 1)
            acts = ", ".join([act.get("name") for act in day.get("activities", [])])
            days_summary.append(f"Day {d_num}: {acts}")
        itin_summary = " | ".join(days_summary)
    except Exception:
        itin_summary = "N/A"
        
    itinerary_context = f"""
Itinerary Context:
Destination: {t.destination}
Duration: {t.duration} Days
Budget Level: {t.budget}
Travel Style: {t.style}
Lodging Options: {lodging_summary}
Schedule Summary: {itin_summary}
"""
    
    # Compile prompt messages
    messages = [
        {"role": "system", "content": f"You are a helpful travel assistant. Answer the user's questions utilizing the itinerary context provided below. Be concise, friendly, and practical.\n{itinerary_context}"}
    ]
    
    # Append dialogue logs
    for h in history[-10:]: # Pass last 10 messages to limit token usage
        messages.append({"role": h.role, "content": h.content})
        
    # Append new user message
    messages.append({"role": "user", "content": req.message})
    
    # Ollama call with cloud fallback
    assistant_reply = ""
    try:
        OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
        
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }
        res = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=5)
        if res.status_code == 200:
            assistant_reply = res.json().get("message", {}).get("content", "")
        else:
            raise Exception(f"Ollama returned non-200: {res.status_code}")
    except Exception as e:
        print(f"Ollama chat offline or failed: {e}. Trying cloud fallback...")
        try:
            # Pollinations AI keyless Cloud Fallback
            pollinations_payload = {
                "messages": messages
            }
            res = requests.post(
                "https://text.pollinations.ai/", 
                json=pollinations_payload, 
                headers={"Content-Type": "application/json"},
                timeout=25
            )
            if res.status_code == 200 and res.text.strip():
                assistant_reply = res.text.strip()
            else:
                raise Exception(f"Pollinations returned status {res.status_code}")
        except Exception as cloud_err:
            print(f"Cloud fallback failed: {cloud_err}")
            # Soft fallback if both are offline
            assistant_reply = f"I'm sorry, I couldn't reach the AI model. Here's what I know about your trip to {t.destination}: It's a {t.duration}-day {t.style.lower()} trip. Let me know if you need help planning accommodations or checking weather!"

    # Save messages to database
    try:
        user_msg = ChatMessage(trip_id=t.id, role="user", content=req.message)
        asst_msg = ChatMessage(trip_id=t.id, role="assistant", content=assistant_reply)
        db.add(user_msg)
        db.add(asst_msg)
        db.commit()
    except Exception as db_err:
        db.rollback()
        print(f"Failed to save chat message: {db_err}")
        
    return {"reply": assistant_reply}

@app.get("/download-pdf/{trip_id}")
def api_download_pdf(trip_id: int, db: Session = Depends(get_db)):
    """
    Reconstructs the trip itinerary dictionary and feeds it to ReportLab,
    returning the compiled PDF as a streaming download.
    """
    t = db.query(Trip).filter(Trip.id == trip_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found.")
        
    # Reassemble trip dictionary
    itinerary_data = {
        "destination": t.destination,
        "duration": t.duration,
        "total_budget_est": t.total_budget_est,
        "budget_breakdown": json.loads(t.budget_breakdown_json) if t.budget_breakdown_json else {},
        "weather": json.loads(t.weather_json) if t.weather_json else {},
        "itinerary": json.loads(t.itinerary_json),
        "accommodations": json.loads(t.accommodations_json) if t.accommodations_json else [],
        "local_flavors": json.loads(t.local_flavors_json) if t.local_flavors_json else {},
        "budget_analysis": {
            "budget_level": t.budget,
            "total_budget": t.total_budget_est
        },
        "travel_tips": [
            "Keep digital copies of all identification on your phone.",
            "Use local public transit cards to save money.",
            "Pack versatile layers as local weather can shift.",
            "Learn key local phrases to connect with residents."
        ]
    }
    
    pdf_buffer = generate_pdf_itinerary(itinerary_data)
    
    # Format clean filename
    safe_city = t.destination.split(",")[0].strip().replace(" ", "_").lower()
    filename = f"itinerary_{safe_city}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.post("/regenerate-activity")
def api_regenerate_activity(req: ActivityRegenRequest, db: Session = Depends(get_db)):
    """
    Regenerates a single activity slot in the itinerary using local Ollama model
    based on a custom prompt, updating the database record.
    """
    t = db.query(Trip).filter(Trip.id == req.trip_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trip record not found.")

    try:
        itinerary = json.loads(t.itinerary_json)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse itinerary JSON from database.")

    # Find the target day and activity slot
    target_day = None
    for day_plan in itinerary:
        if day_plan.get("day") == req.day:
            target_day = day_plan
            break

    if not target_day:
        raise HTTPException(status_code=400, detail=f"Day {req.day} not found in this itinerary.")

    target_activity = None
    target_idx = -1
    for idx, act in enumerate(target_day.get("activities", [])):
        if act.get("time").lower() == req.time_slot.lower():
            target_activity = act
            target_idx = idx
            break

    if not target_activity:
        raise HTTPException(status_code=400, detail=f"Activity slot '{req.time_slot}' not found on Day {req.day}.")

    # Run the regeneration service
    new_activity = regenerate_single_activity(
        destination=t.destination,
        day_num=req.day,
        time_slot=req.time_slot,
        style=t.style,
        budget=t.budget,
        custom_instruction=req.custom_instruction,
        current_activity=target_activity
    )

    # Replace the old activity with the new one
    target_day["activities"][target_idx] = new_activity

    # Save to database
    try:
        t.itinerary_json = json.dumps(itinerary)
        db.commit()
        db.refresh(t)
    except Exception as db_err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(db_err)}")

    # Return the full updated trip (same structure as api_get_trip)
    lat, lon = geocode_destination(t.destination)
    if not lat:
        lat, lon = 48.8566, 2.3522
        
    return {
        "trip_id": t.id,
        "destination": t.destination,
        "duration": t.duration,
        "budget": t.budget,
        "travelers": t.travelers,
        "style": t.style,
        "interests": t.interests.split(",") if t.interests else [],
        "description": f"A custom {t.duration}-day {t.style.lower()} itinerary to {t.destination} for {t.travelers} traveler(s) featuring {t.interests.replace(',', ', ') if t.interests else 'local sights'}.",
        "total_budget_est": t.total_budget_est,
        "budget_breakdown": json.loads(t.budget_breakdown_json) if t.budget_breakdown_json else {},
        "weather": json.loads(t.weather_json) if t.weather_json else {},
        "itinerary": itinerary,
        "accommodations": json.loads(t.accommodations_json) if t.accommodations_json else [],
        "local_flavors": json.loads(t.local_flavors_json) if t.local_flavors_json else {},
        "travel_tips": [
            "Keep digital copies of all identification on your phone.",
            "Use local public transit cards to save money.",
            "Pack versatile layers as local weather can shift.",
            "Learn key local phrases to connect with residents."
        ],
        "latitude": lat,
        "longitude": lon
    }

@app.get("/download-ics/{trip_id}")
def api_download_ics(trip_id: int, db: Session = Depends(get_db)):
    """
    Generates a standard iCalendar (.ics) file mapping each itinerary activity
    to a calendar event, starting from tomorrow.
    """
    t = db.query(Trip).filter(Trip.id == trip_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found.")

    try:
        itinerary = json.loads(t.itinerary_json)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse itinerary JSON.")

    import datetime
    
    # We will schedule the trip starting tomorrow
    start_date = datetime.date.today() + datetime.timedelta(days=1)
    
    # Time slot mapping to hour offset and duration
    time_map = {
        "morning": {"start": (9, 0), "end": (11, 30)},
        "afternoon": {"start": (14, 0), "end": (16, 30)},
        "evening": {"start": (19, 0), "end": (21, 30)}
    }

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Expedition AI//Travel Planner Itinerary//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]

    for day_plan in itinerary:
        d_num = day_plan.get("day", 1)
        event_date = start_date + datetime.timedelta(days=(d_num - 1))
        date_str = event_date.strftime("%Y%m%d")

        for act in day_plan.get("activities", []):
            time_slot = act.get("time", "Morning").lower()
            slot_info = time_map.get(time_slot, {"start": (9, 0), "end": (11, 0)})

            start_time_str = f"{date_str}T{slot_info['start'][0]:02d}{slot_info['start'][1]:02d}00"
            end_time_str = f"{date_str}T{slot_info['end'][0]:02d}{slot_info['end'][1]:02d}00"
            timestamp_str = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

            # Escape special ICS characters
            summary = act.get("name", "Attraction").replace(",", "\\,").replace(";", "\\;")
            desc = act.get("description", "").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
            cost = act.get("cost", "Free")
            duration = act.get("duration", "2 hours")
            
            full_description = f"{desc}\\n\\nCost: {cost}\\nDuration: {duration}\\nStyle: {t.style}"
            location = f"{t.destination}"
            if "lat" in act and "lng" in act:
                location = f"{act['lat']:.5f}\\, {act['lng']:.5f} ({t.destination})"

            uid = f"trip_{t.id}_day_{d_num}_{time_slot}_{slot_info['start'][0]}@expeditionai.local"

            event_lines = [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{timestamp_str}",
                f"DTSTART:{start_time_str}",
                f"DTEND:{end_time_str}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{full_description}",
                f"LOCATION:{location}",
                "END:VEVENT"
            ]
            ics_lines.extend(event_lines)

    ics_lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(ics_lines)
    
    import io
    ics_buffer = io.BytesIO(ics_content.encode("utf-8"))
    
    safe_city = t.destination.split(",")[0].strip().replace(" ", "_").lower()
    filename = f"itinerary_{safe_city}.ics"
    
    return StreamingResponse(
        ics_buffer,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
