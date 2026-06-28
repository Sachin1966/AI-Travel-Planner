import streamlit as st
from streamlit_folium import st_folium
import requests
import json
import os

# Import map generator locally for native rendering
from utils.map_generator import create_folium_map

# Page Setup
st.set_page_config(
    page_title="Expedition AI - Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Endpoint URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Session State Initialization
if "active_trip" not in st.session_state:
    st.session_state.active_trip = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "recent_trips" not in st.session_state:
    st.session_state.recent_trips = []

# Custom CSS for Premium Styling
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

/* Typography & Reset */
html, body, .stApp {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4, h5, h6, .outfit-font {
    font-family: 'Outfit', sans-serif;
}

/* Hide Default Headers & Footers */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Custom Glassmorphism Containers */
.glass-panel {
    background: rgba(17, 24, 39, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
}

.sub-panel {
    background: rgba(31, 41, 55, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 16px;
    margin-top: 10px;
    margin-bottom: 10px;
}

.gradient-text {
    background: linear-gradient(135deg, #a855f7, #6366f1, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}

/* Weather Elements */
.weather-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.08));
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.weather-forecast-day {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 10px;
    border-radius: 8px;
    text-align: center;
}

/* Timeline Components */
.timeline-container {
    border-left: 2px dashed rgba(99, 102, 241, 0.4);
    margin-left: 20px;
    padding-left: 25px;
    position: relative;
}

.timeline-item {
    position: relative;
    margin-bottom: 24px;
}

.timeline-marker {
    position: absolute;
    left: -33px;
    top: 4px;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background-color: #6366F1;
    border: 3px solid var(--background-color, #0f172a);
    box-shadow: 0 0 10px #6366F1;
}

.timeline-time {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 3px;
}

.timeline-name {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 16px;
    color: var(--text-color, #f8fafc);
    margin-bottom: 4px;
}

.timeline-desc {
    color: var(--text-color, #cbd5e1);
    opacity: 0.85;
    font-size: 13.5px;
    margin-bottom: 6px;
    line-height: 1.45;
}

.timeline-meta {
    display: flex;
    gap: 15px;
    font-size: 12px;
    color: var(--text-color, #94a3b8);
    opacity: 0.75;
    margin-bottom: 5px;
}

/* Budget Progress Bars */
.budget-bar-container {
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    height: 10px;
    width: 100%;
    margin-top: 5px;
    margin-bottom: 12px;
    overflow: hidden;
}

.budget-bar-fill {
    height: 100%;
    border-radius: 10px;
}

.sidebar-title {
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 20px;
    text-align: center;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# --- API SERVICES COMMUNICATION ---

def fetch_recent_trips():
    """
    Queries FastAPI for all saved trips in the database.
    """
    try:
        res = requests.get(f"{API_BASE_URL}/trips", timeout=5)
        if res.status_code == 200:
            st.session_state.recent_trips = res.json()
    except Exception:
        st.session_state.recent_trips = []

def fetch_single_trip(trip_id: int):
    """
    Loads details of a selected past trip and resets chat logs.
    """
    with st.spinner("Loading trip..."):
        try:
            res = requests.get(f"{API_BASE_URL}/trip/{trip_id}", timeout=5)
            if res.status_code == 200:
                st.session_state.active_trip = res.json()
                st.session_state.chat_history = []
                st.toast("Loaded trip details!", icon="📂")
            else:
                st.error("Failed to load trip details from server.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")


# Fetch trips on initial load
fetch_recent_trips()


# --- SIDEBAR LAYOUT ---
with st.sidebar:
    st.markdown('<div class="sidebar-title outfit-font"><span class="gradient-text">EXPEDITION AI</span> 🧭</div>', unsafe_allow_html=True)
    
    # Recent Trips History List
    if st.session_state.recent_trips:
        st.markdown("### 📂 Recent Plans")
        for t in st.session_state.recent_trips[:5]: # Show top 5 recent plans
            btn_label = f"🗺️ {t['destination'].split(',')[0]} ({t['duration']}d - {t['budget']})"
            if st.button(btn_label, key=f"trip_history_{t['trip_id']}", use_container_width=True):
                fetch_single_trip(t['trip_id'])
        st.markdown("---")
        
    st.markdown("### 🗺️ New Adventure")
    
    destination = st.text_input("Destination", placeholder="e.g. Paris, Goa, Tokyo...", value="Goa")
    duration = st.slider("Duration (Days)", min_value=1, max_value=10, value=3)
    
    col_trav, col_bud_tier = st.columns(2)
    with col_trav:
        travelers = st.number_input("Travelers", min_value=1, max_value=20, value=1)
    with col_bud_tier:
        budget_tier = st.selectbox("Budget Tier", ["Budget", "Mid-range", "Luxury"], index=1)
        
    budget_value = st.text_input("Estimated Budget (Value)", value="INR 30000", help="Provide budget with currency (e.g. $1500 or INR 30000)")
    
    style = st.selectbox("Travel Style", ["Backpacking", "Budget", "Family", "Adventure", "Luxury"], index=3)
    
    interests = st.multiselect(
        "Interests",
        ["Nature", "Food", "Beaches", "Shopping", "Historical", "Adventure", "Culture", "Wildlife"],
        default=["Beaches", "Food"]
    )
    
    custom_prompt = st.text_area(
        "Special Requests (Optional)",
        placeholder="e.g. Vegetarian only, no long walks, travel with elderly..."
    )
    
    # Generate Plan Trigger
    if st.button("🗺️ Generate Itinerary", type="primary", use_container_width=True):
        payload = {
            "destination": destination,
            "duration": duration,
            "budget": budget_tier,
            "total_budget_val": budget_value,
            "travelers": travelers,
            "style": style,
            "interests": interests,
            "custom_prompt": custom_prompt
        }
        
        with st.spinner("Designing your itinerary..."):
            try:
                res = requests.post(f"{API_BASE_URL}/generate-itinerary", json=payload, timeout=95)
                if res.status_code == 200:
                    st.session_state.active_trip = res.json()
                    st.session_state.chat_history = []
                    st.success("Plan created successfully!")
                    fetch_recent_trips() # Reload history list
                else:
                    err_msg = res.json().get("detail", "Generation error")
                    st.error(f"Backend Server Error: {err_msg}")
                    st.info("Check if your Ollama instance is serving.")
            except Exception as e:
                st.error(f"Could not connect to API server at {API_BASE_URL}.")
                st.info("Start the FastAPI backend with: `uvicorn backend.api:app` and try again.")


# --- MAIN SCREEN INTERFACE ---
if st.session_state.active_trip:
    t = st.session_state.active_trip
    trip_id = t.get("trip_id")
    
    # 1. HEADER BANNER CARD
    st.markdown(
        f"""
        <div class="glass-panel">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                <div>
                    <span style="font-size:12px; font-weight:700; color:#6366F1; text-transform:uppercase; letter-spacing:0.1em;">Generated Itinerary</span>
                    <h1 style="margin: 0; font-size:42px; font-weight:800; color:#f8fafc;">{t.get('destination')}</h1>
                    <p style="margin: 10px 0 0 0; color:#cbd5e1; font-size:15px; max-width:800px; line-height:1.5;">{t.get('description')}</p>
                </div>
                <div style="text-align:right; min-width:200px;">
                    <div style="font-size:13px; color:#94a3b8; font-weight:600;">ESTIMATED TOTAL BUDGET</div>
                    <div style="font-size:32px; font-weight:800; color:#10b981;">{t.get('total_budget_est')}</div>
                    <span style="background-color:rgba(99,102,241,0.15); color:#a855f7; font-size:11px; padding:4px 10px; border-radius:30px; font-weight:bold;">
                        📅 {t.get('duration')} Days • 👥 {t.get('travelers')} Traveler(s) • 💳 {t.get('budget')} ({t.get('style')})
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 2. COLUMN LAYOUT: Left = Dashboards, Right = Widgets & Chat
    col_content, col_widgets = st.columns([2, 1])
    
    with col_content:
        # Dashboard Views
        tab_timeline, tab_map, tab_hotels, tab_food = st.tabs([
            "📅 Schedule Timeline",
            "🗺️ Interactive Route Map",
            "🏨 Lodging Recommendations",
            "🍽️ Food & Local Specialties"
        ])
        
        # TAB 1: DAY SCHEDULE TIMELINE
        with tab_timeline:
            st.markdown("### Daily Itinerary Plan")
            for day_idx, day_plan in enumerate(t.get("itinerary", [])):
                d_num = day_plan.get("day", day_idx + 1)
                d_theme = day_plan.get("theme", "Exploration")
                
                with st.expander(f"📅 Day {d_num} — {d_theme}", expanded=(d_num == 1)):
                    colors = ["#a855f7", "#10b981", "#3b82f6"] # Morning, Afternoon, Evening
                    
                    for a_idx, act in enumerate(day_plan.get("activities", [])):
                        color = colors[a_idx % len(colors)]
                        st.markdown(
                            f"""
                            <div class="timeline-container" style="margin-bottom: 0px; padding-bottom: 0px;">
                                <div class="timeline-item" style="margin-bottom: 5px;">
                                    <div class="timeline-marker" style="background-color:{color}; box-shadow:0 0 10px {color};"></div>
                                    <div class="timeline-time" style="color:{color};">{act.get('time', 'Activity')}</div>
                                    <div class="timeline-name">{act.get('name')}</div>
                                    <div class="timeline-desc">{act.get('description')}</div>
                                    <div class="timeline-meta">
                                        <span>⏱️ <b>Duration:</b> {act.get('duration', '2 hours')}</span>
                                        <span>💰 <b>Cost:</b> {act.get('cost', 'Free')}</span>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Swap activity widget
                        with st.expander(f"🔄 Swap {act.get('time')} Slot", expanded=False):
                            with st.form(key=f"swap_form_{d_num}_{act.get('time')}"):
                                swap_instr = st.text_input(
                                    "What would you prefer instead?",
                                    placeholder="e.g. Visit a museum, outdoor hiking, beach sunset...",
                                    key=f"swap_input_{d_num}_{act.get('time')}"
                                )
                                submit_swap = st.form_submit_button("Replace Activity")
                                if submit_swap and swap_instr:
                                    payload = {
                                        "trip_id": trip_id,
                                        "day": d_num,
                                        "time_slot": act.get("time"),
                                        "custom_instruction": swap_instr
                                    }
                                    with st.spinner("Swapping activity..."):
                                        try:
                                            res = requests.post(f"{API_BASE_URL}/regenerate-activity", json=payload, timeout=50)
                                            if res.status_code == 200:
                                                st.session_state.active_trip = res.json()
                                                st.toast(f"Swapped {act.get('time')} activity successfully!", icon="🔄")
                                                st.rerun()
                                            else:
                                                st.error("Failed to swap activity. Try again.")
                                        except Exception as e:
                                            st.error(f"Error connecting to backend: {e}")
                    
        # TAB 2: INTERACTIVE FOLIUM MAP
        with tab_map:
            st.markdown("### Interactive Itinerary Route Map")
            try:
                map_obj = create_folium_map(t)
                st_folium(map_obj, width="100%", height=500, returned_objects=[])
            except Exception as e:
                st.error(f"Error rendering interactive map: {e}")
                
        # TAB 3: ACCOMMODATIONS
        with tab_hotels:
            st.markdown("### Lodging Suggestions")
            cols_hotels = st.columns(min(3, len(t.get("accommodations", []))))
            
            for h_idx, hotel in enumerate(t.get("accommodations", [])):
                with cols_hotels[h_idx % len(cols_hotels)]:
                    st.markdown(
                        f"""
                        <div class="glass-panel" style="padding:20px; height:100%;">
                            <span style="background-color:rgba(16,185,129,0.1); color:#10b981; font-size:11px; padding:3px 8px; border-radius:30px; font-weight:bold;">
                                {hotel.get('type', 'Stay')}
                            </span>
                            <h4 style="margin: 8px 0 4px 0; color:#f8fafc; font-size:16px;">{hotel.get('name')}</h4>
                            <div style="color:#f59e0b; font-size:13px; font-weight:bold; margin-bottom:8px;">Price Tier: {hotel.get('approx_price', hotel.get('price_level', '$$'))}</div>
                            <p style="color:#cbd5e1; font-size:12.5px; line-height:1.4; margin:0;">{hotel.get('description', hotel.get('address', ''))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
        # TAB 4: LOCAL FLAVORS
        with tab_food:
            flavors = t.get("local_flavors", {})
            st.markdown("### Culinary Delicacies & Local Specialties")
            
            col_dish, col_drink = st.columns(2)
            with col_dish:
                st.markdown("<h4 style='color:#a855f7;'>🍽️ Famous Dishes</h4>", unsafe_allow_html=True)
                for dish in flavors.get("cuisines", []):
                    st.markdown(
                        f"""
                        <div class="sub-panel">
                            <div style="font-weight:700; color:#f8fafc; font-size:14px;">{dish.get('name')}</div>
                            <div style="color:#cbd5e1; font-size:12px; margin-top:2px;">{dish.get('description')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            with col_drink:
                st.markdown("<h4 style='color:#06b6d4;'>🍹 Signature Drinks</h4>", unsafe_allow_html=True)
                for bev in flavors.get("beverages", []):
                    st.markdown(
                        f"""
                        <div class="sub-panel">
                            <div style="font-weight:700; color:#f8fafc; font-size:14px;">{bev.get('name')}</div>
                            <div style="color:#cbd5e1; font-size:12px; margin-top:2px;">{bev.get('description')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
            if flavors.get("hotspots"):
                st.markdown(
                    f"""
                    <div class="glass-panel" style="margin-top:15px; border-left:4px solid #6366f1; padding:15px 20px;">
                        <h4 style="margin:0 0 5px 0; color:#f8fafc; font-size:15px;">📍 Recommended Dining Areas</h4>
                        <p style="margin:0; color:#cbd5e1; font-size:13px; line-height:1.4;">{flavors.get('hotspots')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # 3. RIGHT PANEL WIDGETS
    with col_widgets:
        
        # PDF DOWNLOAD BUTTON (Direct streaming from API)
        try:
            pdf_url = f"{API_BASE_URL}/download-pdf/{trip_id}"
            pdf_res = requests.get(pdf_url, timeout=10)
            if pdf_res.status_code == 200:
                st.download_button(
                    label="📥 Download PDF Itinerary",
                    data=pdf_res.content,
                    file_name=f"itinerary_{t.get('destination').split(',')[0].strip().lower()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception:
            st.error("PDF endpoint offline. Ensure backend is running.")

        # ICS CALENDAR DOWNLOAD BUTTON
        try:
            ics_url = f"{API_BASE_URL}/download-ics/{trip_id}"
            ics_res = requests.get(ics_url, timeout=10)
            if ics_res.status_code == 200:
                st.download_button(
                    label="📅 Sync to Calendar (.ics)",
                    data=ics_res.content,
                    file_name=f"itinerary_{t.get('destination').split(',')[0].strip().lower()}.ics",
                    mime="text/calendar",
                    use_container_width=True
                )
        except Exception:
            st.error("Calendar Sync endpoint offline.")
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # WEATHER WIDGET
        weather = t.get("weather")
        if weather:
            st.markdown(
                f"""
                <div class="glass-panel" style="padding:20px; margin-bottom:15px;">
                    <h3 style="margin:0 0 12px 0; font-size:18px; color:#f8fafc;">🌤️ Weather Report</h3>
                    <div class="weather-card">
                        <div>
                            <div style="font-size:36px; font-weight:800; color:#f8fafc;">{weather.get('temp')}°C</div>
                            <div style="font-size:14px; color:#cbd5e1; font-weight:600; margin-top:2px;">
                                {weather.get('emoji', '🌡️')} {weather.get('description', 'Sunny')}
                            </div>
                        </div>
                        <div style="text-align:right; font-size:12px; color:#94a3b8; line-height:1.4;">
                            <div>💨 Wind: {weather.get('wind_speed')} km/h</div>
                            <div>📍 Current Weather</div>
                        </div>
                    </div>
                    <div style="font-size:12.5px; color:#cbd5e1; margin-top:12px; line-height:1.4; border-top:1px solid #334155; padding-top:10px;">
                        💡 <b>Travel Advice:</b> {weather.get('advice')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # BUDGET ALLOCATION WIDGET
        breakdown = t.get("budget_breakdown", {})
        if breakdown:
            st.markdown('<div class="glass-panel" style="padding:20px; margin-bottom:15px;">', unsafe_allow_html=True)
            st.markdown('<h3 style="margin:0 0 15px 0; font-size:18px; color:#f8fafc;">📊 Budget Analysis</h3>', unsafe_allow_html=True)
            
            cat_colors = {
                "Accommodations": "#10b981",  # Emerald
                "Food & Drinks": "#06b6d4",   # Cyan
                "Activities": "#a855f7",      # Purple
                "Transport": "#f59e0b",       # Amber
                "Miscellaneous": "#ef4444"     # Red
            }
            
            for category, pct in breakdown.items():
                color = cat_colors.get(category, "#6366F1")
                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:space-between; font-size:12.5px; color:#cbd5e1; font-weight:500;">
                        <span>{category}</span>
                        <span style="color:#ffffff; font-weight:700;">{pct}%</span>
                    </div>
                    <div class="budget-bar-container">
                        <div class="budget-bar-fill" style="width: {pct}%; background-color: {color}; box-shadow: 0 0 8px {color}80;"></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            # Savings tips
            savings_tips = t.get("budget_analysis", {}).get("savings_suggestions", [])
            if savings_tips:
                st.markdown("<div style='font-size:12.5px; font-weight:700; color:#94a3b8; margin-top:12px;'>💸 SAVINGS TIPS:</div>", unsafe_allow_html=True)
                for tip in savings_tips[:2]: # Show top 2 tips
                    st.markdown(f"<div style='font-size:11.5px; color:#cbd5e1; margin-top:4px;'>• {tip}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # 4. CHAT ASSISTANT PANEL
        st.markdown('<div class="glass-panel" style="padding:20px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin:0 0 10px 0; font-size:18px; color:#f8fafc;">💬 Travel Chat Assistant</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:11.5px; color:#94a3b8; margin-top:-5px; margin-bottom:15px;">Ask questions regarding this itinerary (e.g. "What is on day 2?").</p>', unsafe_allow_html=True)
        
        # Render scrollable history
        chat_box = st.container(height=250)
        with chat_box:
            # Welcome message if empty
            if not st.session_state.chat_history:
                st.markdown(f"<div style='font-size:12.5px; color:#94a3b8; text-align:center; padding-top:20px;'>Ask me anything about your trip to {t.get('destination')}!</div>", unsafe_allow_html=True)
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(f"<div style='font-size:12.5px;'>{msg['content']}</div>", unsafe_allow_html=True)
                    
        # User input box
        if chat_input := st.chat_input("Ask a travel question..."):
            # Add to state and render immediately
            st.session_state.chat_history.append({"role": "user", "content": chat_input})
            with chat_box:
                with st.chat_message("user"):
                    st.markdown(f"<div style='font-size:12.5px;'>{chat_input}</div>", unsafe_allow_html=True)
            
            # Request backend reply
            payload = {
                "trip_id": trip_id,
                "message": chat_input
            }
            try:
                res = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=50)
                if res.status_code == 200:
                    reply = res.json().get("reply")
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    with chat_box:
                        with st.chat_message("assistant"):
                            st.markdown(f"<div style='font-size:12.5px;'>{reply}</div>", unsafe_allow_html=True)
                else:
                    st.error("Failed to get chatbot reply.")
            except Exception as e:
                st.error(f"Connection error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # Blank state (App opened first time)
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 75vh; text-align: center;">
            <div style="font-size: 76px; margin-bottom: 20px; animation: bounce 2s infinite;">🧭</div>
            <h1 style="font-size: 42px; font-weight: 800; margin-bottom: 12px; color:#f8fafc;">Expedition AI Travel Planner</h1>
            <p style="font-size: 16px; color: #cbd5e1; max-width: 580px; line-height: 1.6; margin-bottom: 30px;">
                Decoupled FastAPI backend, SQLite database persistence, ReportLab PDF generators, and local Ollama intelligence rolled into a single beautiful dashboard.
            </p>
            <div style="display: flex; gap: 15px; flex-wrap:wrap; justify-content:center;">
                <span style="background: rgba(99, 102, 241, 0.12); color:#6366F1; border: 1px solid rgba(99, 102, 241, 0.25); font-size:12px; padding:8px 16px; border-radius:30px; font-weight:bold;">
                    ⚡ FastAPI Endpoints
                </span>
                <span style="background: rgba(16, 185, 129, 0.12); color:#10B981; border: 1px solid rgba(16, 185, 129, 0.25); font-size:12px; padding:8px 16px; border-radius:30px; font-weight:bold;">
                    💾 SQLite Database Persistence
                </span>
                <span style="background: rgba(168, 85, 247, 0.12); color:#A855F7; border: 1px solid rgba(168, 85, 247, 0.25); font-size:12px; padding:8px 16px; border-radius:30px; font-weight:bold;">
                    📥 ReportLab PDF Exports
                </span>
            </div>
            <div style="margin-top: 40px; font-size: 13px; color: #94a3b8; background-color: rgba(30, 41, 59, 0.5); padding: 12px 24px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05);">
                👉 <b>Getting Started:</b> Make sure the FastAPI server is running with <code>uvicorn backend.api:app --reload</code>, then configure your parameters on the sidebar!
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
