import folium

def create_itinerary_map(itinerary_data):
    """
    Creates a styled, interactive Folium map mapping out the travel itinerary.
    """
    center_lat = itinerary_data.get("latitude", 48.8566)
    center_lon = itinerary_data.get("longitude", 2.3522)
    
    # Initialize Folium Map with a premium Dark Matter tile style to match our dark theme
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        control_scale=True,
        tiles="CartoDB dark_matter"
    )
    
    # Track points to draw a sequential travel path line and fit bounds
    all_points = []
    
    # Day-specific colors to group activities visually
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
    
    # Iterate through each day and place sequential markers
    for day_idx, day_plan in enumerate(itinerary_data.get("itinerary", [])):
        color = day_colors[day_idx % len(day_colors)]
        day_num = day_plan.get("day", day_idx + 1)
        theme = day_plan.get("theme", "Explore")
        
        for act_idx, act in enumerate(day_plan.get("activities", [])):
            lat = act.get("lat")
            lng = act.get("lng")
            if not lat or not lng:
                continue
                
            point = [lat, lng]
            all_points.append(point)
            
            # Format timeslots and labels
            time_slot = act.get("time", "Activity")
            act_name = act.get("name", "Stop")
            act_desc = act.get("description", "")
            cost = act.get("cost", "Free")
            duration = act.get("duration", "N/A")
            
            # HTML Popup matching the overall premium aesthetic
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
            
            # Create a numbered circular HTML badge to show the sequence on the map
            # Example: "1.2" = Day 1, Activity 2
            badge_text = f"{day_num}.{act_idx + 1}"
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
                transition: transform 0.2s;
            " onmouseover="this.style.transform='scale(1.2)';" onmouseout="this.style.transform='scale(1.0)';">
                {badge_text}
            </div>
            """
            
            # Draw popup and marker
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

    # Draw a line connecting the travel path sequentially
    if len(all_points) > 1:
        # Subtle dotted/dashed line linking the itinerary sequence
        folium.PolyLine(
            locations=all_points,
            color="#6366F1",  # Primary Indigo Theme
            weight=3,
            opacity=0.6,
            dash_array="5, 8",
            tooltip="Itinerary Route"
        ).add_to(m)
        
        # Fit bounds to ensure all points are visible
        m.fit_bounds(all_points, padding=[30, 30])
        
    return m
