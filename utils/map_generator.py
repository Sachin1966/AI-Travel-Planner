import folium
import requests

def get_road_route(points: list) -> list:
    """
    Queries the free, keyless OSRM API to get the roadway routing coordinates between points.
    Returns a list of [lat, lon] coordinate pairs along actual roads.
    """
    if len(points) < 2:
        return points
        
    # OSRM expects coordinates in "lon,lat" format separated by semicolons
    coords_str = ";".join([f"{lon},{lat}" for lat, lon in points])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    
    headers = {"User-Agent": "ExpeditionAITravelPlanner/1.0 (contact: asach@github.com)"}
    try:
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            data = res.json()
            routes = data.get("routes", [])
            if routes:
                geometry = routes[0].get("geometry", {})
                coordinates = geometry.get("coordinates", [])
                if coordinates:
                    return [[lat, lon] for lon, lat in coordinates]
    except Exception as e:
        print(f"OSRM routing failed: {e}")
    return points # Fallback to straight lines if OSRM fails

def create_folium_map(itinerary_data: dict):
    """
    Renders an interactive Folium Map containing markers for all attractions and hotels,
    color-coded by day and sequentially numbered, connected by real road-driving routes.
    """
    center_lat = itinerary_data.get("latitude", 48.8566)
    center_lon = itinerary_data.get("longitude", 2.3522)
    
    # Initialize Map with premium Dark Matter tiles
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        control_scale=True,
        tiles="CartoDB dark_matter"
    )
    
    all_points = []
    
    day_colors = [
        "#A855F7",  # Day 1: Purple
        "#10B981",  # Day 2: Emerald
        "#3B82F6",  # Day 3: Blue
        "#F59E0B",  # Day 4: Amber
        "#EF4444",  # Day 5: Red
        "#06B6D4",  # Day 6: Cyan
        "#EC4899",  # Day 7: Pink
        "#84CC16",  # Day 8: Lime
    ]
    
    # Plot Hotels
    for h_idx, hotel in enumerate(itinerary_data.get("accommodations", [])):
        lat = hotel.get("lat")
        lon = hotel.get("lng")
        if not lat or not lon:
            lat = center_lat + 0.005 + (h_idx * 0.002)
            lon = center_lon - 0.005 - (h_idx * 0.002)
        
        hotel_html = f"""
        <div style="font-family:'Outfit','Inter',sans-serif; min-width:200px; max-width:250px; color:#f8fafc; background-color:#1e293b; padding:8px; border-radius:6px;">
            <h4 style="margin:0 0 4px 0; color:#10b981; font-size:13px;">🏨 Lodging Suggestion</h4>
            <div style="font-weight:600; font-size:12.5px; color:#ffffff;">{hotel.get('name')}</div>
            <div style="font-size:11px; color:#cbd5e1; margin-top:2px;">{hotel.get('description')}</div>
            <div style="font-size:10px; color:#f59e0b; font-weight:bold; margin-top:4px;">Rating: {hotel.get('rating', '4.0')}★ • {hotel.get('price_level', '$$')}</div>
        </div>
        """
        
        iframe = folium.IFrame(hotel_html, width=250, height=110)
        popup = folium.Popup(iframe, max_width=250)
        
        folium.Marker(
            location=[lat, lon],
            popup=popup,
            icon=folium.Icon(color="green", icon="home", prefix="fa"),
            tooltip=f"Hotel: {hotel.get('name')}"
        ).add_to(m)
        
    # Plot Itinerary activities chronologically and build routes day-by-day
    for d_idx, day_plan in enumerate(itinerary_data.get("itinerary", [])):
        color = day_colors[d_idx % len(day_colors)]
        day_num = day_plan.get("day", d_idx + 1)
        day_points = []
        
        for a_idx, act in enumerate(day_plan.get("activities", [])):
            lat = act.get("lat")
            lng = act.get("lng")
            if not lat or not lng:
                continue
                
            point = [lat, lng]
            day_points.append(point)
            all_points.append(point)
            
            time_slot = act.get("time", "Activity")
            act_name = act.get("name", "Stop")
            act_desc = act.get("description", "")
            cost = act.get("cost", "Free")
            duration = act.get("duration", "2 hours")
            
            popup_html = f"""
            <div style="
                font-family: 'Outfit', 'Inter', sans-serif; 
                min-width: 220px; 
                max-width: 280px; 
                color: #f8fafc;
                background-color: #0f172a;
                padding: 10px;
                border-radius: 8px;
            ">
                <h4 style="margin: 0 0 5px 0; color: {color}; font-weight: 700; font-size: 14px;">Day {day_num} • {time_slot}</h4>
                <div style="font-weight: 600; font-size: 13px; margin-bottom: 6px; color: #ffffff;">{act_name}</div>
                <p style="margin: 0 0 8px 0; font-size: 11.5px; color: #cbd5e1; line-height: 1.4;">{act_desc}</p>
                <div style="display: flex; justify-content: space-between; font-size: 10px; color: #94a3b8; border-top: 1px solid #334155; padding-top: 6px; margin-top: 4px;">
                    <span>⏱️ {duration}</span>
                    <span>💰 {cost}</span>
                </div>
            </div>
            """
            
            badge_text = f"{day_num}.{a_idx + 1}"
            html_badge = f"""
            <div style="
                background-color: #0f172a;
                border: 2.5px solid {color};
                border-radius: 50%;
                color: #ffffff;
                font-family: 'Outfit', 'Inter', sans-serif;
                font-weight: 700;
                text-align: center;
                width: 32px;
                height: 32px;
                line-height: 27px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
                font-size: 11px;
                cursor: pointer;
            ">
                {badge_text}
            </div>
            """
            
            iframe = folium.IFrame(popup_html, width=280, height=160)
            popup = folium.Popup(iframe, max_width=280)
            
            folium.Marker(
                location=point,
                popup=popup,
                icon=folium.DivIcon(
                    html=html_badge,
                    icon_size=(32, 32),
                    icon_anchor=(16, 16)
                ),
                tooltip=f"Day {day_num} • {time_slot}: {act_name}"
            ).add_to(m)
            
        # Draw roadway route for this specific day
        if len(day_points) > 1:
            road_coords = get_road_route(day_points)
            folium.PolyLine(
                locations=road_coords,
                color=color,
                weight=4.5,
                opacity=0.85,
                tooltip=f"Day {day_num} Roadway Route"
            ).add_to(m)

    # Auto-adjust zoom to fit all plotted points
    if all_points:
        m.fit_bounds(all_points, padding=[30, 30])
        
    return m
