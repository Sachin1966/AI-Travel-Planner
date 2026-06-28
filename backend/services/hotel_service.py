import os
import requests
import random
from dotenv import load_dotenv
from utils.helpers import geocode_destination, get_destination_currency, nominatim_request

load_dotenv()

AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID", "")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET", "")

def fetch_hotels(destination: str, budget_level: str):
    """
    Attempts to fetch lodging recommendations from the Amadeus Travel API.
    Falls back to a mock generator on missing credentials or API error.
    """
    if AMADEUS_CLIENT_ID.strip() and AMADEUS_CLIENT_SECRET.strip():
        try:
            token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            token_data = {
                "grant_type": "client_credentials",
                "client_id": AMADEUS_CLIENT_ID,
                "client_secret": AMADEUS_CLIENT_SECRET
            }
            token_res = requests.post(token_url, data=token_data, timeout=5)
            if token_res.status_code == 200:
                access_token = token_res.json().get("access_token")
                lat, lon = geocode_destination(destination)
                if lat:
                    hotel_list_url = f"https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-geomap?latitude={lat}&longitude={lon}&radius=10&ratings=3,4,5"
                    headers = {"Authorization": f"Bearer {access_token}"}
                    hotel_res = requests.get(hotel_list_url, headers=headers, timeout=5)
                    if hotel_res.status_code == 200:
                        raw_hotels = hotel_res.json().get("data", [])
                        processed_hotels = []
                        for h in raw_hotels[:6]:
                            rating = h.get("rating", 4)
                            tier = "Mid-range" if rating == 3 else ("Luxury" if rating == 5 else "Mid-range")
                            price_map = {"Budget": "$40 - $70", "Mid-range": "$120 - $220", "Luxury": "$350 - $600"}
                            processed_hotels.append({
                                "name": h.get("name", "Unknown Hotel").title(),
                                "rating": rating,
                                "approx_price": price_map.get(tier, "$100"),
                                "address": f"City Center, {destination.title()}",
                                "amenities": ["Free Wi-Fi", "AC", "Breakfast", "Bar", "Pool"][:rating],
                                "type": tier
                            })
                        if processed_hotels:
                            return processed_hotels
        except Exception as e:
            print(f"Amadeus Hotel API failed: {e}. Falling back to mock generator.")
            
    return _generate_mock_hotels(destination, budget_level)

def _generate_mock_hotels(destination: str, budget_level: str):
    dest_clean = destination.lower().strip()
    
    flagship_hotels = {
        "paris": [
            {"name": "Hôtel Regina Louvre", "rating": 5.0, "approx_price": "€480/night", "address": "2 Place des Pyramides, Paris", "amenities": ["Spa", "Eiffel View", "Bar", "Gym"], "type": "Luxury"},
            {"name": "Plaza Athénée", "rating": 5.0, "approx_price": "€850/night", "address": "25 Avenue Montaigne, Paris", "amenities": ["Spa", "Michelin Dining", "Balcony"], "type": "Luxury"},
            {"name": "Hôtel Britannique Paris", "rating": 4.2, "approx_price": "€180/night", "address": "20 Rue Victoria, Paris", "amenities": ["Wi-Fi", "AC", "Shuttle", "Breakfast"], "type": "Mid-range"},
            {"name": "Hotel Caron de Beaumarchais", "rating": 4.3, "approx_price": "€210/night", "address": "12 Rue Vieille-du-Temple, Paris", "amenities": ["Antique Decor", "Wi-Fi", "Breakfast"], "type": "Mid-range"},
            {"name": "Les Piaules Nation Hostel", "rating": 4.0, "approx_price": "€45/night", "address": "28 Boulevard de Charonne, Paris", "amenities": ["Co-working", "Rooftop Bar", "Kitchen"], "type": "Budget"},
            {"name": "Generator Paris", "rating": 4.1, "approx_price": "€38/night", "address": "9-11 Place du Colonel Fabien, Paris", "amenities": ["Rooftop Terrace", "Cafe & Bar", "Laundry"], "type": "Budget"}
        ],
        "tokyo": [
            {"name": "Park Hyatt Tokyo", "rating": 5.0, "approx_price": "¥92,000/night", "address": "3-7-1 Nishi-Shinjuku, Tokyo", "amenities": ["Indoor Pool", "Peak Bar", "Spa", "Gym"], "type": "Luxury"},
            {"name": "Aman Tokyo", "rating": 5.0, "approx_price": "¥140,000/night", "address": "1-5-6 Otemachi, Tokyo", "amenities": ["Onsen Spa", "Sake Bar", "Zen View"], "type": "Luxury"},
            {"name": "Hotel Gracery Shinjuku", "rating": 4.3, "approx_price": "¥22,000/night", "address": "1-19-1 Kabukicho, Tokyo", "amenities": ["Godzilla Terrace", "Wi-Fi", "Massage"], "type": "Mid-range"},
            {"name": "Shibuya Stream Excel Hotel Tokyu", "rating": 4.4, "approx_price": "¥28,000/night", "address": "3-21-3 Shibuya, Tokyo", "amenities": ["Modern Bar", "Wi-Fi", "Fitness"], "type": "Mid-range"},
            {"name": "Nine Hours Capsule Hotel", "rating": 4.1, "approx_price": "¥5,800/night", "address": "3-10-1 Misakicho, Tokyo", "amenities": ["Futuristic Capsule", "Lounge", "Lockers"], "type": "Budget"},
            {"name": "Bunka Hostel Tokyo", "rating": 4.2, "approx_price": "¥6,200/night", "address": "1-13-5 Asakusa, Tokyo", "amenities": ["Sake Bar", "Clean Dorms", "Kitchenette"], "type": "Budget"}
        ],
        "goa": [
            {"name": "Taj Exotica Resort & Spa", "rating": 4.9, "approx_price": "₹28,000/night", "address": "Benaulim, Goa", "amenities": ["Private Beach", "Golf", "Jiva Spa", "Pool"], "type": "Luxury"},
            {"name": "The Leela Goa", "rating": 5.0, "approx_price": "₹34,000/night", "address": "Mobor Beach, Goa", "amenities": ["Private Lagoon", "Golf Course", "Spa", "Butler"], "type": "Luxury"},
            {"name": "Lemon Tree Amarante", "rating": 4.1, "approx_price": "₹6,500/night", "address": "Candolim, Goa", "amenities": ["Pool", "Spa", "Wi-Fi", "Restaurant", "Bar"], "type": "Mid-range"},
            {"name": "Acron Waterfront Resort", "rating": 4.4, "approx_price": "₹9,200/night", "address": "Baga Peninsula, Goa", "amenities": ["Riverfront Pool", "Jacuzzi", "Wi-Fi"], "type": "Mid-range"},
            {"name": "Zostel Goa (Anjuna)", "rating": 4.3, "approx_price": "₹1,200/night", "address": "Anjuna, Goa", "amenities": ["Social Cafe", "Bicycle Rental", "Common Lounge"], "type": "Budget"},
            {"name": "The Hosteller Goa", "rating": 4.2, "approx_price": "₹950/night", "address": "Morjim, Goa", "amenities": ["Pool", "Cafe", "Hammocks", "Workstation"], "type": "Budget"}
        ],
        "new york": [
            {"name": "The Plaza Hotel", "rating": 5.0, "approx_price": "$850/night", "address": "Fifth Ave at Central Park, New York", "amenities": ["Champagne Bar", "Guerlain Spa", "Butler"], "type": "Luxury"},
            {"name": "The St. Regis New York", "rating": 5.0, "approx_price": "$980/night", "address": "Two E 55th St, New York", "amenities": ["Butler Service", "Bentley Car", "King Cole Bar"], "type": "Luxury"},
            {"name": "Arlo NoMad", "rating": 4.2, "approx_price": "$210/night", "address": "11 E 31st St, New York", "amenities": ["Rooftop Bar", "Micro-rooms", "Wi-Fi"], "type": "Mid-range"},
            {"name": "The Jane Hotel", "rating": 4.1, "approx_price": "$140/night", "address": "113 Jane St, New York", "amenities": ["Vintage Cabin", "Free Bikes", "Ballroom"], "type": "Mid-range"},
            {"name": "Freehand New York", "rating": 4.0, "approx_price": "$90/night", "address": "23 Lexington Ave, New York", "amenities": ["Social Bars", "Custom Art", "Game Room"], "type": "Budget"},
            {"name": "HI New York City Hostel", "rating": 4.2, "approx_price": "$65/night", "address": "891 Amsterdam Ave, New York", "amenities": ["Large Patio", "Wi-Fi", "Weekly Events"], "type": "Budget"}
        ],
        "london": [
            {"name": "The Ritz London", "rating": 5.0, "approx_price": "£780/night", "address": "150 Piccadilly, London", "amenities": ["Michelin Dining", "Ritz Club", "Chauffeur"], "type": "Luxury"},
            {"name": "The Savoy", "rating": 5.0, "approx_price": "£820/night", "address": "Strand, London", "amenities": ["American Bar", "Savoy Grill", "Butler"], "type": "Luxury"},
            {"name": "CitizenM Tower of London", "rating": 4.4, "approx_price": "£190/night", "address": "40 Trinity Square, London", "amenities": ["iPad Controls", "24/7 Buffet", "Rooftop Bar"], "type": "Mid-range"},
            {"name": "The Hoxton, Shoreditch", "rating": 4.3, "approx_price": "£220/night", "address": "81 Great Eastern St, London", "amenities": ["Trendy Lobby Bar", "Wi-Fi", "Local Snacks"], "type": "Mid-range"},
            {"name": "Wombat's City Hostel", "rating": 4.1, "approx_price": "£50/night", "address": "7 Dock St, London", "amenities": ["Wombar Club", "Kitchen", "Lockers"], "type": "Budget"},
            {"name": "Palmers Lodge Swiss Cottage", "rating": 4.2, "approx_price": "£38/night", "address": "40 College Cres, London", "amenities": ["Victorian Mansion", "On-site Bar", "Gardens"], "type": "Budget"}
        ],
        "rome": [
            {"name": "Rome Cavalieri, Waldorf Astoria", "rating": 5.0, "approx_price": "€520/night", "address": "Via Alberto Cadlolo 101, Rome", "amenities": ["Michelin Dining", "Grand Spa", "Gardens"], "type": "Luxury"},
            {"name": "Hotel Hassler Roma", "rating": 5.0, "approx_price": "€780/night", "address": "Piazza Trinità dei Monti 6, Rome", "amenities": ["Panoramic View", "Spa", "Garden Bar"], "type": "Luxury"},
            {"name": "Hotel Nazionale Rome", "rating": 4.3, "approx_price": "€175/night", "address": "Piazza di Monte Citorio 131, Rome", "amenities": ["Square View", "Wi-Fi", "Breakfast", "Bar"], "type": "Mid-range"},
            {"name": "iQ Hotel Roma", "rating": 4.5, "approx_price": "€210/night", "address": "Via Firenze 8, Rome", "amenities": ["Rooftop Terrace", "Sauna & Tub", "Laundry"], "type": "Mid-range"},
            {"name": "The Beehive Hostel Rome", "rating": 4.2, "approx_price": "€42/night", "address": "Via Marghera 8, Rome", "amenities": ["Organic Cafe", "Garden", "Kitchen"], "type": "Budget"},
            {"name": "Generator Rome", "rating": 4.0, "approx_price": "€35/night", "address": "Via Principe Amedeo 257, Rome", "amenities": ["Bistro", "Rooftop Lounge", "Wi-Fi"], "type": "Budget"}
        ],
        "mumbai": [
            {"name": "The Taj Mahal Palace", "rating": 5.0, "approx_price": "₹32,000/night", "address": "Colaba, Mumbai", "amenities": ["Harbor View", "Spa", "Pool", "10 Dining Venues"], "type": "Luxury"},
            {"name": "The Oberoi Mumbai", "rating": 5.0, "approx_price": "₹35,000/night", "address": "Nariman Point, Mumbai", "amenities": ["Sea View", "24/7 Butler", "Gym", "Spa"], "type": "Luxury"},
            {"name": "Fariyas Hotel Colaba", "rating": 4.1, "approx_price": "₹7,200/night", "address": "Colaba, Mumbai", "amenities": ["Pool", "Gym", "Dining", "Bar"], "type": "Mid-range"},
            {"name": "Gordon House Hotel", "rating": 4.3, "approx_price": "₹8,500/night", "address": "Colaba, Mumbai", "amenities": ["Themed Rooms", "Nightclub", "Wi-Fi"], "type": "Mid-range"},
            {"name": "Backpacker Panda Colaba", "rating": 4.2, "approx_price": "₹1,400/night", "address": "Colaba, Mumbai", "amenities": ["Social Lounge", "AC", "Wi-Fi"], "type": "Budget"},
            {"name": "Zostel Mumbai", "rating": 4.4, "approx_price": "₹1,600/night", "address": "Andheri East, Mumbai", "amenities": ["Rooftop Cafe", "Cinema Lounge", "AC"], "type": "Budget"}
        ],
        "sydney": [
            {"name": "Park Hyatt Sydney", "rating": 5.0, "approx_price": "A$880/night", "address": "7 Hickson Rd, The Rocks, Sydney", "amenities": ["Opera View", "Heated Pool", "Butler"], "type": "Luxury"},
            {"name": "The Langham Sydney", "rating": 5.0, "approx_price": "A$650/night", "address": "89 Kent St, Sydney", "amenities": ["Roman Pool", "Spa", "Harbour View"], "type": "Luxury"},
            {"name": "Ovolo 1888 Darling Harbour", "rating": 4.5, "approx_price": "A$240/night", "address": "139 Murray St, Pyrmont, Sydney", "amenities": ["Industrial Chic", "Bar", "Social Hour"], "type": "Mid-range"},
            {"name": "Little National Hotel", "rating": 4.4, "approx_price": "A$210/night", "address": "26 Clarence St, Sydney", "amenities": ["Rooftop Library Bar", "Smart Rooms"], "type": "Mid-range"},
            {"name": "Wake Up! Sydney Central", "rating": 4.3, "approx_price": "A$65/night", "address": "509 Pitt St, Sydney", "amenities": ["Cafe & Bar", "Free Tours", "Trivia Night"], "type": "Budget"},
            {"name": "Sydney Harbour YHA", "rating": 4.4, "approx_price": "A$72/night", "address": "110 Cumberland St, Sydney", "amenities": ["Rooftop View", "Kitchen", "Weekly BBQ"], "type": "Budget"}
        ],
        "berlin": [
            {"name": "Hotel Adlon Kempinski", "rating": 5.0, "approx_price": "€460/night", "address": "Unter den Linden 77, Berlin", "amenities": ["Gate Views", "Michelin Dining", "Pool"], "type": "Luxury"},
            {"name": "Soho House Berlin", "rating": 5.0, "approx_price": "€510/night", "address": "Torstrasse 1, Berlin", "amenities": ["Rooftop Pool", "Screening Room", "Spa"], "type": "Luxury"},
            {"name": "Michelberger Hotel", "rating": 4.3, "approx_price": "€140/night", "address": "Warschauer Str. 39, Berlin", "amenities": ["Courtyard Gigs", "Organic Food", "Sauna"], "type": "Mid-range"},
            {"name": "25hours Bikini Berlin", "rating": 4.5, "approx_price": "€195/night", "address": "Budapester Str. 40, Berlin", "amenities": ["Monkey Bar", "Zoo View", "Sauna"], "type": "Mid-range"},
            {"name": "Circus Hostel Berlin", "rating": 4.4, "approx_price": "€42/night", "address": "Weinbergsweg 1A, Berlin", "amenities": ["Microbrewery", "Social Lounge", "Tours"], "type": "Budget"},
            {"name": "EastSeven Berlin Hostel", "rating": 4.3, "approx_price": "€36/night", "address": "Schwedter Str. 7, Berlin", "amenities": ["BBQ Garden", "Kitchen", "Free Wi-Fi"], "type": "Budget"}
        ],
        "singapore": [
            {"name": "Marina Bay Sands", "rating": 5.0, "approx_price": "S$780/night", "address": "10 Bayfront Ave, Singapore", "amenities": ["Infinity Pool", "Casino", "Spa", "Observation Deck"], "type": "Luxury"},
            {"name": "Raffles Hotel Singapore", "rating": 5.0, "approx_price": "S$1,100/night", "address": "1 Beach Rd, Singapore", "amenities": ["Historic Long Bar", "Raffles Butler", "Courtyard"], "type": "Luxury"},
            {"name": "The Warehouse Hotel", "rating": 4.5, "approx_price": "S$320/night", "address": "320 Havelock Rd, Singapore", "amenities": ["Heritage Building", "Rooftop Pool", "Cocktail Bar"], "type": "Mid-range"},
            {"name": "Oasia Hotel Downtown", "rating": 4.4, "approx_price": "S$260/night", "address": "100 Peck Seah St, Singapore", "amenities": ["Skyscraper Greenery", "Pools", "Gym"], "type": "Mid-range"},
            {"name": "Dream Lodge Singapore", "rating": 4.3, "approx_price": "S$68/night", "address": "172 Tyrwhitt Rd, Singapore", "amenities": ["Pod-style Beds", "AC", "Free Breakfast"], "type": "Budget"},
            {"name": "Wink Capsule Hostel", "rating": 4.2, "approx_price": "S$55/night", "address": "8A Mosque St, Singapore", "amenities": ["Smart Capsule", "Chinatown Location", "Lounge"], "type": "Budget"}
        ],
        "dubai": [
            {"name": "Burj Al Arab Jumeirah", "rating": 5.0, "approx_price": "AED 4,800/night", "address": "Jumeirah St, Dubai", "amenities": ["Private Beach", "Helipad", "Gold iPads", "Butler"], "type": "Luxury"},
            {"name": "Atlantis The Palm", "rating": 4.9, "approx_price": "AED 2,500/night", "address": "The Palm Jumeirah, Dubai", "amenities": ["Waterpark", "Aquarium", "Michelin Dining"], "type": "Luxury"},
            {"name": "Rove Downtown Dubai", "rating": 4.5, "approx_price": "AED 380/night", "address": "312 Al Sa'ada St, Dubai", "amenities": ["Burj View Pool", "Cinema", "24/7 Gym"], "type": "Mid-range"},
            {"name": "Manzil Downtown Dubai", "rating": 4.4, "approx_price": "AED 580/night", "address": "Sheikh Mohammed Boulevard, Dubai", "amenities": ["Arabian Courtyard", "Pool", "Gym"], "type": "Mid-range"},
            {"name": "Gateway Hotel Dubai", "rating": 4.1, "approx_price": "AED 180/night", "address": "Bur Dubai, Dubai", "amenities": ["Sauna", "Wi-Fi", "Pool", "Shuttle"], "type": "Budget"},
            {"name": "Citymax Hotel Bur Dubai", "rating": 4.0, "approx_price": "AED 150/night", "address": "Kuwait Street, Dubai", "amenities": ["Rooftop Pool", "Sports Bar", "Shuttle"], "type": "Budget"}
        ],
        "cairo": [
            {"name": "Marriott Mena House", "rating": 5.0, "approx_price": "E£ 14,000/night", "address": "Giza, Cairo", "amenities": ["Pyramids View", "Palace Gardens", "Spa", "Pool"], "type": "Luxury"},
            {"name": "The Nile Ritz-Carlton", "rating": 5.0, "approx_price": "E£ 16,500/night", "address": "Downtown, Cairo", "amenities": ["Nile Views", "Olympic Pool", "Rooftop Lounge"], "type": "Luxury"},
            {"name": "Steigenberger El Tahrir", "rating": 4.5, "approx_price": "E£ 4,800/night", "address": "Tahrir Square, Cairo", "amenities": ["Central", "Pool", "Sauna", "Gym"], "type": "Mid-range"},
            {"name": "Kempinski Nile Hotel", "rating": 4.6, "approx_price": "E£ 6,200/night", "address": "Garden City, Cairo", "amenities": ["Rooftop Pool", "Nile Promenade", "Butler"], "type": "Mid-range"},
            {"name": "Dahab Hostel Cairo", "rating": 4.1, "approx_price": "E£ 650/night", "address": "Downtown, Cairo", "amenities": ["Bedouin Rooftop", "Kitchen", "Wi-Fi"], "type": "Budget"},
            {"name": "Heritage Hostel Cairo", "rating": 4.3, "approx_price": "E£ 800/night", "address": "Tahrir Square, Cairo", "amenities": ["Museum View", "AC", "Shuttle", "Free Tea"], "type": "Budget"}
        ]
    }
    
    for key, hotels in flagship_hotels.items():
        if key in dest_clean:
            return hotels
            
    # Try dynamic Nominatim lookup for real hotels
    try:
        currency_symbol, currency_code = get_destination_currency(destination)
        
        city = destination.split(",")[0].strip()
        url = f"https://nominatim.openstreetmap.org/search?q=hotels+in+{requests.utils.quote(city)}&format=json&limit=15&addressdetails=1"
        data = nominatim_request(url)
        if data:
                processed = []
                for item in data:
                    name = item.get("display_name", "").split(",")[0].strip()
                    if not name or len(name) < 4 or name.isdigit():
                        continue
                    if any(char.isdigit() for char in name[:3]):
                        continue
                        
                    lat = float(item.get("lat"))
                    lon = float(item.get("lon"))
                    addr = ", ".join(item.get("display_name", "").split(",")[1:4]).strip()
                    
                    name_lower = name.lower()
                    if any(k in name_lower for k in ["hostel", "yha", "backpacker", "guesthouse", "lodge", "dorm"]):
                        tier = "Budget"
                        price = f"{currency_symbol}{random.randint(1500, 3000)}/night" if currency_code == "INR" else f"{currency_symbol}{random.randint(30, 60)}/night"
                        amenities = ["Free Wi-Fi", "Common Kitchen", "Bicycle Rental", "Social Lounge"]
                        rating = round(random.uniform(3.8, 4.3), 1)
                    elif any(k in name_lower for k in ["taj", "resort", "palace", "plaza", "grand", "ritz", "savoy", "hyatt", "oberoi", "marriott"]):
                        tier = "Luxury"
                        price = f"{currency_symbol}{random.randint(15000, 30000)}/night" if currency_code == "INR" else f"{currency_symbol}{random.randint(350, 800)}/night"
                        amenities = ["Infinity Pool", "Wellness Spa", "Fine Dining", "24/7 Butler", "Valet"]
                        rating = round(random.uniform(4.7, 5.0), 1)
                    else:
                        tier = "Mid-range"
                        price = f"{currency_symbol}{random.randint(5000, 10000)}/night" if currency_code == "INR" else f"{currency_symbol}{random.randint(120, 220)}/night"
                        amenities = ["Free Wi-Fi", "AC", "Breakfast Included", "Fitness Center"]
                        rating = round(random.uniform(4.2, 4.6), 1)
                        
                    processed.append({
                        "name": name,
                        "rating": rating,
                        "approx_price": price,
                        "address": addr if addr else f"Central {city}",
                        "amenities": amenities,
                        "type": tier,
                        "lat": lat,
                        "lng": lon
                    })
                if len(processed) >= 3:
                    return processed[:6]
    except Exception as e:
        print(f"Dynamic hotels lookup failed: {e}. Falling back to default list.")
        
    city = destination.split(",")[0].strip().title()
    
    # Try to geocode the city center for the fallback hotel markers
    lat, lon = geocode_destination(destination)
    if not lat:
        lat, lon = 48.8566, 2.3522
        
    return [
        {
            "name": f"The Royal Palace & Spa {city}",
            "rating": 4.9,
            "approx_price": "$450/night" if budget_level == "Luxury" else "$350 - $550/night",
            "address": f"101 Grand Boulevard, {city}",
            "amenities": ["Infinity Pool", "Wellness Spa", "Fine Dining Room", "24/7 Butler Service"],
            "type": "Luxury",
            "lat": lat + 0.003,
            "lng": lon - 0.003
        },
        {
            "name": f"Boutique Hotel Center Suites {city}",
            "rating": 4.2,
            "approx_price": "$160/night" if budget_level == "Mid-range" else "$120 - $220/night",
            "address": f"45 Cathedral Way, {city}",
            "amenities": ["Free Wi-Fi", "Complimentary Breakfast", "Airport Shuttle"],
            "type": "Mid-range",
            "lat": lat + 0.005,
            "lng": lon - 0.005
        },
        {
            "name": f"Central Backpackers & Hostels {city}",
            "rating": 4.0,
            "approx_price": "$40/night" if budget_level == "Budget" else "$30 - $60/night",
            "address": f"12 Station Street, {city}",
            "amenities": ["Social Bar", "Shared Kitchen", "Free City Maps"],
            "type": "Budget",
            "lat": lat + 0.007,
            "lng": lon - 0.007
        }
    ]
