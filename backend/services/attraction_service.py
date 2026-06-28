import os
import requests
import random
from dotenv import load_dotenv
from utils.helpers import geocode_destination, nominatim_request

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

def fetch_attractions(destination: str, interests: list):
    """
    Attempts to fetch points of interest using the Google Places API.
    Falls back to a mock builder that generates 10 attractions matching the interests.
    """
    if GOOGLE_PLACES_API_KEY.strip():
        try:
            lat, lon = geocode_destination(destination)
            if lat:
                query_str = f"top tourist attractions in {destination}"
                url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={requests.utils.quote(query_str)}&key={GOOGLE_PLACES_API_KEY}"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    raw_places = res.json().get("results", [])
                    processed = []
                    for p in raw_places[:10]:
                        geom = p.get("geometry", {}).get("location", {})
                        processed.append({
                            "name": p.get("name"),
                            "description": p.get("formatted_address", "Scenic spot"),
                            "rating": p.get("rating", 4.0),
                            "lat": geom.get("lat", lat),
                            "lng": geom.get("lng", lon)
                        })
                    if processed:
                        return processed
        except Exception as e:
            print(f"Google Places API failed: {e}. Falling back to mock generator.")
            
    return _generate_mock_attractions(destination, interests)

def _generate_mock_attractions(destination: str, interests: list):
    dest_clean = destination.lower().strip()
    
    flagship_attractions = {
        "paris": [
            {"name": "Eiffel Tower", "description": "The iconic iron tower featuring city observation decks.", "rating": 4.7, "lat": 48.8584, "lng": 2.2945},
            {"name": "Louvre Museum", "description": "World's largest museum housing the Mona Lisa and classics.", "rating": 4.8, "lat": 48.8606, "lng": 2.3376},
            {"name": "Notre-Dame Cathedral", "description": "Famed medieval Gothic cathedral on the Seine.", "rating": 4.7, "lat": 48.8530, "lng": 2.3499},
            {"name": "Sacré-Cœur Basilica", "description": "Hilltop white-domed church providing panoramic views.", "rating": 4.6, "lat": 48.8867, "lng": 2.3431},
            {"name": "Musée d'Orsay", "description": "Stunning former train station housing Impressionist masterworks.", "rating": 4.8, "lat": 48.8599, "lng": 2.3265},
            {"name": "Arc de Triomphe", "description": "Colossal triumphal arch honoring war victories.", "rating": 4.7, "lat": 48.8738, "lng": 2.2950},
            {"name": "Jardin du Luxembourg", "description": "Gorgeous 17th-century royal gardens containing fountains.", "rating": 4.6, "lat": 48.8462, "lng": 2.3371},
            {"name": "Palace of Versailles", "description": "The lavish principal royal residence of French kings.", "rating": 4.7, "lat": 48.8049, "lng": 2.1204},
            {"name": "Centre Pompidou", "description": "High-tech marvel showcasing modern art collections.", "rating": 4.4, "lat": 48.8606, "lng": 2.3522},
            {"name": "Sainte-Chapelle", "description": "Medieval Gothic chapel famous for its stained glass.", "rating": 4.8, "lat": 48.8554, "lng": 2.3450}
        ],
        "tokyo": [
            {"name": "Senso-ji Temple", "description": "Tokyo's oldest and most iconic Buddhist temple in Asakusa.", "rating": 4.7, "lat": 35.7148, "lng": 139.7967},
            {"name": "Tokyo Skytree", "description": "Futuristic observation tower offering stunning views of Mt. Fuji.", "rating": 4.6, "lat": 35.7101, "lng": 139.8107},
            {"name": "Shibuya Crossing", "description": "The world's busiest pedestrian scramble with neon billboards.", "rating": 4.5, "lat": 35.6595, "lng": 139.7004},
            {"name": "Meiji Jingu Shrine", "description": "A tranquil Shinto shrine nestled inside a dense forest.", "rating": 4.6, "lat": 35.6764, "lng": 139.6993},
            {"name": "Shinjuku Gyoen", "description": "Sprawling imperial garden featuring cherry blossoms.", "rating": 4.6, "lat": 35.6852, "lng": 139.7101},
            {"name": "Tsukiji Outer Market", "description": "Lively alleys filled with fresh sushi stalls and street food.", "rating": 4.4, "lat": 35.6655, "lng": 139.7702},
            {"name": "Akihabara Town", "description": "The neon-lit global hub of anime, gaming, and electronics.", "rating": 4.3, "lat": 35.6997, "lng": 139.7715},
            {"name": "Odaiba Seaside Park", "description": "Man-made island district with a Statue of Liberty replica.", "rating": 4.4, "lat": 35.6264, "lng": 139.7798},
            {"name": "Tokyo Tower", "description": "Retro red-and-white lattice tower offering observation decks.", "rating": 4.5, "lat": 35.6586, "lng": 139.7454},
            {"name": "Imperial Palace Gardens", "description": "The ruins of Edo Castle's innermost defenses.", "rating": 4.4, "lat": 35.6850, "lng": 139.7528}
        ],
        "goa": [
            {"name": "Baga Beach", "description": "Goa's most famous lively beach, known for shacks and sports.", "rating": 4.3, "lat": 15.5553, "lng": 73.7517},
            {"name": "Basilica of Bom Jesus", "description": "16th-century church housing the tomb of St. Francis Xavier.", "rating": 4.6, "lat": 15.5009, "lng": 73.9116},
            {"name": "Fort Aguada", "description": "Portuguese fort and lighthouse overlooking the Arabian Sea.", "rating": 4.4, "lat": 15.4925, "lng": 73.7735},
            {"name": "Dudhsagar Falls", "description": "Spectacular four-tiered waterfall cascading down East Goa.", "rating": 4.5, "lat": 15.3179, "lng": 74.3143},
            {"name": "Anjuna Flea Market", "description": "Bohemian beachside flea market selling spices and crafts.", "rating": 4.1, "lat": 15.5794, "lng": 73.7423},
            {"name": "Palolem Beach", "description": "Beautiful crescent beach in South Goa, famous for calm waters.", "rating": 4.6, "lat": 15.0100, "lng": 74.0232},
            {"name": "Se Cathedral", "description": "Gigantic 16th-century Portuguese church in Old Goa.", "rating": 4.5, "lat": 15.5036, "lng": 73.9126},
            {"name": "Mangueshi Temple", "description": "400-year-old temple dedicated to Shiva with deepastambha tower.", "rating": 4.6, "lat": 15.4439, "lng": 73.9681},
            {"name": "Calangute Beach", "description": "Popular beach crowded with endless food shacks and markets.", "rating": 4.2, "lat": 15.5436, "lng": 73.7550},
            {"name": "Spice Plantation Tour", "description": "Guided walks through spice gardens with Goan lunch.", "rating": 4.5, "lat": 15.4190, "lng": 74.0150}
        ],
        "new york": [
            {"name": "Statue of Liberty", "description": "Iconic copper statue on Liberty Island with museum tours.", "rating": 4.7, "lat": 40.6892, "lng": -74.0445},
            {"name": "Central Park", "description": "Sprawling urban park with paths, lakes, zoo, and lawns.", "rating": 4.8, "lat": 40.7829, "lng": -73.9654},
            {"name": "Empire State Building", "description": "Classic Art Deco skyscraper featuring observation decks.", "rating": 4.7, "lat": 40.7484, "lng": -73.9857},
            {"name": "Metropolitan Museum of Art", "description": "Elite art museum, spanning 5,000 years of global culture.", "rating": 4.8, "lat": 40.7794, "lng": -73.9632},
            {"name": "Times Square", "description": "Brightly illuminated hub of Broadway theaters and neon lights.", "rating": 4.5, "lat": 40.7580, "lng": -73.9855},
            {"name": "Brooklyn Bridge", "description": "Historic suspension bridge offering city skyline views.", "rating": 4.8, "lat": 40.7061, "lng": -73.9969},
            {"name": "High Line Park", "description": "Elevated public park built on a historic disused rail line.", "rating": 4.6, "lat": 40.7480, "lng": -74.0048},
            {"name": "9/11 Memorial Museum", "description": "Moving tribute and museum honoring victims of September 11.", "rating": 4.8, "lat": 40.7115, "lng": -74.0131},
            {"name": "Rockefeller Center", "description": "Vast midtown complex famous for the winter ice rink.", "rating": 4.6, "lat": 40.7587, "lng": -73.7787},
            {"name": "Grand Central Terminal", "description": "Beautiful historic railway terminal with a celestial ceiling.", "rating": 4.7, "lat": 40.7527, "lng": -73.9772}
        ],
        "london": [
            {"name": "British Museum", "description": "World-famous museum dedicated to human history and relics.", "rating": 4.7, "lat": 51.5194, "lng": -0.1270},
            {"name": "Tower of London", "description": "Historic castle housing the Crown Jewels and guards.", "rating": 4.6, "lat": 51.5081, "lng": -0.0759},
            {"name": "London Eye", "description": "Giant observation wheel on the South Bank overlooking the Thames.", "rating": 4.5, "lat": 51.5033, "lng": -0.1195},
            {"name": "Tower Bridge", "description": "Iconic Victorian suspension bridge with glass floor walkways.", "rating": 4.7, "lat": 51.5055, "lng": -0.0754},
            {"name": "Westminster Abbey", "description": "Historic Gothic abbey, the site of royal coronations.", "rating": 4.7, "lat": 51.4994, "lng": -0.1273},
            {"name": "Buckingham Palace", "description": "The administrative residence of the UK reigning monarch.", "rating": 4.5, "lat": 51.5014, "lng": -0.1419},
            {"name": "Hyde Park", "description": "Vast royal park containing the Serpentine lake.", "rating": 4.6, "lat": 51.5073, "lng": -0.1657},
            {"name": "Natural History Museum", "description": "Interactive museum containing prehistoric dinosaur skeletons.", "rating": 4.7, "lat": 51.4967, "lng": -0.1764},
            {"name": "Tate Modern", "description": "Former power station converted into an international art gallery.", "rating": 4.5, "lat": 51.5076, "lng": -0.0994},
            {"name": "Big Ben & Parliament", "description": "The landmark Palace of Westminster and iconic clock tower.", "rating": 4.6, "lat": 51.5007, "lng": -0.1246}
        ],
        "rome": [
            {"name": "Colosseum", "description": "The colossal ancient Roman amphitheater used for gladiators.", "rating": 4.8, "lat": 41.8902, "lng": 12.4922},
            {"name": "Trevi Fountain", "description": "Baroque masterwork fountain; toss a coin to guarantee return.", "rating": 4.7, "lat": 41.9009, "lng": 12.4833},
            {"name": "Pantheon", "description": "Well-preserved 2nd-century Roman temple with a colossal dome.", "rating": 4.8, "lat": 41.8986, "lng": 12.4769},
            {"name": "Roman Forum", "description": "Vast archaeological site containing government ruins.", "rating": 4.6, "lat": 41.8925, "lng": 12.4853},
            {"name": "Vatican Sistine Chapel", "description": "Elite collections of classic sculptures and frescoes.", "rating": 4.7, "lat": 41.9065, "lng": 12.4536},
            {"name": "St. Peter's Basilica", "description": "The largest church building in Christendom, designed by masters.", "rating": 4.8, "lat": 41.9022, "lng": 12.4539},
            {"name": "Piazza Navona", "description": "Elegant Baroque plaza showcasing Bernini's fountains.", "rating": 4.6, "lat": 41.8989, "lng": 12.4731},
            {"name": "Spanish Steps", "description": "A monumental staircase climbing from Piazza di Spagna.", "rating": 4.5, "lat": 41.9060, "lng": 12.4828},
            {"name": "Castel Sant'Angelo", "description": "Historic cylindrical fortress on the Tiber River.", "rating": 4.6, "lat": 41.9031, "lng": 12.4663},
            {"name": "Villa Borghese Gardens", "description": "Sprawling landscaped gardens hosting art galleries.", "rating": 4.6, "lat": 41.9131, "lng": 12.4867}
        ],
        "mumbai": [
            {"name": "Gateway of India", "description": "Grand basalt arch monument built on the Mumbai waterfront.", "rating": 4.6, "lat": 18.9220, "lng": 72.8347},
            {"name": "Marine Drive", "description": "Scenic 3.6-kilometer beachfront promenade along Back Bay.", "rating": 4.6, "lat": 18.9415, "lng": 72.8237},
            {"name": "C.S.M. Terminus", "description": "UNESCO World Heritage station featuring Victorian Gothic styling.", "rating": 4.7, "lat": 18.9400, "lng": 72.8354},
            {"name": "Colaba Causeway Market", "description": "Bustling street market selling artifacts and street food.", "rating": 4.2, "lat": 18.9138, "lng": 72.8276},
            {"name": "Sanjay Gandhi National Park", "description": "Large forest reserve inside city limits with Kanheri Caves.", "rating": 4.4, "lat": 19.2291, "lng": 72.9182},
            {"name": "Haji Ali Dargah", "description": "Historic mosque and tomb located on an islet off Worli.", "rating": 4.6, "lat": 18.9827, "lng": 72.8089},
            {"name": "Elephanta Caves", "description": "Rock-cut cave temples dedicated to Shiva on Elephanta Island.", "rating": 4.4, "lat": 18.9633, "lng": 72.9315},
            {"name": "Siddhivinayak Temple", "description": "Highly popular Hindu temple dedicated to Lord Ganesha.", "rating": 4.8, "lat": 19.0169, "lng": 72.8302},
            {"name": "Juhu Beach", "description": "Vibrant beach famous for local street food snacks.", "rating": 4.1, "lat": 19.0988, "lng": 72.8264},
            {"name": "CSM Vastu Museum", "description": "Premier art and history museum housed in a majestic building.", "rating": 4.6, "lat": 18.9269, "lng": 72.8327}
        ],
        "sydney": [
            {"name": "Sydney Opera House", "description": "Iconic multi-venue performing arts center in Sydney Harbour.", "rating": 4.8, "lat": -33.8568, "lng": 151.2153},
            {"name": "Sydney Harbour Bridge", "description": "Steel arch bridge across Sydney Harbour offering bridge climbs.", "rating": 4.7, "lat": -33.8523, "lng": 151.2108},
            {"name": "Bondi Beach", "description": "Famed crescent of golden sand and surf, popular with locals.", "rating": 4.6, "lat": -33.8908, "lng": 151.2743},
            {"name": "Royal Botanic Garden", "description": "State-heritage-listed botanic garden adjacent to the CBD.", "rating": 4.6, "lat": -33.8642, "lng": 151.2166},
            {"name": "Darling Harbour", "description": "Lively waterfront pedestrian precinct loaded with attractions.", "rating": 4.5, "lat": -33.8749, "lng": 151.2009},
            {"name": "Taronga Zoo", "description": "Scenic city-side harbor zoo featuring Australian wildlife.", "rating": 4.6, "lat": -33.8435, "lng": 151.2413},
            {"name": "The Rocks", "description": "Historic area with cobblestone streets, pubs, and markets.", "rating": 4.4, "lat": -33.8588, "lng": 151.2076},
            {"name": "Art Gallery of NSW", "description": "Main public gallery in Sydney displaying classic/indigenous art.", "rating": 4.5, "lat": -33.8688, "lng": 151.2175},
            {"name": "Hyde Park Sydney", "description": "Australia's oldest public parkland containing war memorials.", "rating": 4.4, "lat": -33.8732, "lng": 151.2113},
            {"name": "Manly Beach", "description": "Popular northern beach offering ferry rides and surf.", "rating": 4.5, "lat": -33.7997, "lng": 151.2848}
        ],
        "berlin": [
            {"name": "Brandenburg Gate", "description": "18th-century neoclassical monument, symbol of peace and unity.", "rating": 4.7, "lat": 52.5163, "lng": 13.3777},
            {"name": "Reichstag Building", "description": "Historic parliament building featuring a glass dome landmark.", "rating": 4.6, "lat": 52.5186, "lng": 13.3761},
            {"name": "Museum Island", "description": "UNESCO World Heritage site housing 5 world-class museums.", "rating": 4.7, "lat": 52.5206, "lng": 13.3986},
            {"name": "Berlin Wall Memorial", "description": "Exhibition memorializing the division of Berlin.", "rating": 4.6, "lat": 52.5350, "lng": 13.3902},
            {"name": "East Side Gallery", "description": "Open-air memorial gallery painted on a section of the wall.", "rating": 4.5, "lat": 52.5050, "lng": 13.4397},
            {"name": "Alexanderplatz & TV Tower", "description": "Huge public square and Europe's tallest observation tower.", "rating": 4.5, "lat": 52.5208, "lng": 13.4094},
            {"name": "Checkpoint Charlie", "description": "Famous Cold War border crossing point between East and West.", "rating": 4.1, "lat": 52.5074, "lng": 13.3904},
            {"name": "Charlottenburg Palace", "description": "Lavish baroque palace featuring beautiful gardens.", "rating": 4.5, "lat": 52.5201, "lng": 13.2957},
            {"name": "Tiergarten Park", "description": "Sprawling central park with lawns, lakes, and monuments.", "rating": 4.6, "lat": 52.5145, "lng": 13.3501},
            {"name": "Memorial Church", "description": "Spire-damaged church left as a memorial to peace.", "rating": 4.4, "lat": 52.5048, "lng": 13.3352}
        ],
        "singapore": [
            {"name": "Gardens by the Bay", "description": "Futuristic park featuring Supertree structures and domes.", "rating": 4.8, "lat": 1.2816, "lng": 103.8636},
            {"name": "Marina Bay Sands SkyPark", "description": "Rooftop observation deck offering panoramic city views.", "rating": 4.7, "lat": 1.2838, "lng": 103.8591},
            {"name": "Sentosa Island", "description": "Resort island with sandy beaches, golf, and dining.", "rating": 4.5, "lat": 1.2494, "lng": 103.8303},
            {"name": "Universal Studios", "description": "Theme park featuring movie-themed rides and attractions.", "rating": 4.6, "lat": 1.2540, "lng": 103.8238},
            {"name": "Singapore Botanic Gardens", "description": "160-year-old tropical garden, a UNESCO World Heritage site.", "rating": 4.7, "lat": 1.3138, "lng": 103.8159},
            {"name": "Chinatown Singapore", "description": "Bustling ethnic enclave with historic temples and street food.", "rating": 4.5, "lat": 1.2823, "lng": 103.8442},
            {"name": "Little India", "description": "Vibrant neighborhood with shops, temples, and spice aromas.", "rating": 4.5, "lat": 1.3069, "lng": 103.8492},
            {"name": "Clarke Quay", "description": "Vibrant riverside quay packed with bars and restaurants.", "rating": 4.4, "lat": 1.2905, "lng": 103.8465},
            {"name": "Singapore Flyer", "description": "Giant observation wheel offering skyline views.", "rating": 4.5, "lat": 1.2893, "lng": 103.8631},
            {"name": "Merlion Park", "description": "Waterfront park housing the iconic half-fish, half-lion statue.", "rating": 4.5, "lat": 1.2868, "lng": 103.8545}
        ],
        "dubai": [
            {"name": "Burj Khalifa", "description": "The world's tallest building, offering observation decks.", "rating": 4.8, "lat": 25.1972, "lng": 55.2744},
            {"name": "The Dubai Mall", "description": "Massive shopping and entertainment mall with an aquarium.", "rating": 4.7, "lat": 25.1985, "lng": 55.2796},
            {"name": "Palm Jumeirah", "description": "Famous man-made palm-tree-shaped archipelago.", "rating": 4.6, "lat": 25.1124, "lng": 55.1390},
            {"name": "Burj Al Arab Lookout", "description": "Famed sail-shaped hotel beachfront photo spot.", "rating": 4.6, "lat": 25.1412, "lng": 55.1862},
            {"name": "Dubai Marina Walk", "description": "Waterfront promenade lined with cafes and skyscrapers.", "rating": 4.6, "lat": 25.0783, "lng": 55.1403},
            {"name": "Dubai Miracle Garden", "description": "Massive flower garden displaying unique structures.", "rating": 4.5, "lat": 25.0596, "lng": 55.2444},
            {"name": "Gold & Spice Souks", "description": "Traditional markets selling jewelry, spices, and shawls.", "rating": 4.3, "lat": 25.2678, "lng": 55.2974},
            {"name": "Jumeirah Mosque", "description": "Stunning mosque offering guided educational cultural tours.", "rating": 4.6, "lat": 25.2337, "lng": 55.2654},
            {"name": "Global Village", "description": "Seasonal cultural park offering international pavilions.", "rating": 4.6, "lat": 25.0680, "lng": 55.3090},
            {"name": "Dubai Frame", "description": "Giant picture frame monument presenting old and new Dubai.", "rating": 4.5, "lat": 25.2355, "lng": 55.3004}
        ],
        "cairo": [
            {"name": "Pyramids of Giza", "description": "Ancient monumental royal tombs, including the Great Sphinx.", "rating": 4.8, "lat": 29.9792, "lng": 31.1342},
            {"name": "The Egyptian Museum", "description": "Historic museum housing Tutankhamun treasures.", "rating": 4.6, "lat": 30.0478, "lng": 31.2336},
            {"name": "Khan el-Khalili Bazaar", "description": "Historic open-air bazaar filled with spices and crafts.", "rating": 4.5, "lat": 30.0477, "lng": 31.2622},
            {"name": "Cairo Citadel", "description": "Medieval Islamic fortification housing landmark mosques.", "rating": 4.6, "lat": 30.0299, "lng": 31.2611},
            {"name": "Al-Azhar Park", "description": "Hilltop green park offering panoramic views of old Cairo.", "rating": 4.6, "lat": 30.0409, "lng": 31.2651},
            {"name": "Coptic Cairo", "description": "Historic Christian quarter containing ancient churches.", "rating": 4.5, "lat": 30.0059, "lng": 31.2301},
            {"name": "Mosque of Muhammad Ali", "description": "Alabaster mosque offering views from the Citadel heights.", "rating": 4.6, "lat": 30.0287, "lng": 31.2599},
            {"name": "Nile Felucca Ride", "description": "Traditional wooden sailboats cruising on the Nile.", "rating": 4.4, "lat": 30.0435, "lng": 31.2243},
            {"name": "Cairo Tower", "description": "Observation tower presenting vistas of the Nile and city.", "rating": 4.3, "lat": 30.0459, "lng": 31.2243},
            {"name": "Hanging Church", "description": "Famed historic Coptic church built over a Roman gatehouse.", "rating": 4.6, "lat": 30.0053, "lng": 31.2302}
        ]
    }
    
    for key, places in flagship_attractions.items():
        if key in dest_clean:
            return places
            
    # Try dynamic Nominatim lookup for real attractions
    try:
        city = destination.split(",")[0].strip()
        url = f"https://nominatim.openstreetmap.org/search?q=tourist+attractions+in+{requests.utils.quote(city)}&format=json&limit=35&addressdetails=1"
        data = nominatim_request(url)
        if data:
                processed = []
                for item in data:
                    name = item.get("display_name", "").split(",")[0].strip()
                    if not name or len(name) < 3 or name.isdigit():
                        continue
                        
                    lat = float(item.get("lat"))
                    lon = float(item.get("lon"))
                    
                    desc = f"Discover the historical {name}, an iconic tourist destination in the heart of {city} offering unique local experiences."
                    rating = round(random.uniform(4.3, 4.9), 1)
                    
                    processed.append({
                        "name": name,
                        "description": desc,
                        "rating": rating,
                        "lat": lat,
                        "lng": lon
                    })
                if len(processed) >= 3:
                    return processed
    except Exception as e:
        print(f"Dynamic attractions lookup failed: {e}. Falling back to default list.")
        
    lat, lon = geocode_destination(destination)
    if not lat:
        lat, lon = 48.8566, 2.3522 # Default center
        
    interest_pool = {
        "Nature": [
            ("Green Valley Park", "Serene botanical garden and wildlife sanctuary with walking trails."),
            ("Mountain Peak Viewpoint", "Lookout deck offering panoramic views of the scenic ridges."),
            ("River Gorges & Waterfall", "Magnificent natural waterfalls surrounded by forest hiking paths.")
        ],
        "Historical": [
            ("Central Heritage Museum", "Showcasing local archaeological findings and historical relics."),
            ("Ancient Fortress Ruins", "Medieval stone fortifications overlooking the city valleys."),
            ("Historic Memorial Arch", "Monument commemorating the city's founders and historic milestones.")
        ],
        "Culture": [
            ("St. Paul's Cathedral", "Magnificent cathedral featuring beautiful stained glass and architecture."),
            ("Traditional Art Center", "Museum displaying locally crafted pottery, weaving, and oil paintings."),
            ("Royal Palace Gardens", "Wander through the historic royal residence and formal gardens.")
        ],
        "Food": [
            ("Artisanal Chocolate Factory", "Interactive tours showing local spice-infused chocolate making."),
            ("Central Food Bazaar", "Vibrant marketplace alleys loaded with fresh regional street eats."),
            ("Heritage Winery Gardens", "Local vineyards offering scenic grape walks and barrel tastings.")
        ],
        "Beaches": [
            ("Sunny Bay Shoreline", "Golden sand beaches perfect for swimming, water sports, and sunsets."),
            ("Secret Cove Cliffs", "Quiet, secluded rocky inlet bordered by palms and turquoise waves."),
            ("Fisherman's Wharf Pier", "Historic boardwalk populated by seafood shacks and boat charters.")
        ],
        "Adventure": [
            ("Climbing Ridge Trails", "Rugged rocky ascents providing high-adrenaline climbing and views."),
            ("Canyon Zip-Line Launch", "High-speed canopy rides zooming across deep river valleys."),
            ("Kayaking Bay Rentals", "Rent water gear to paddle past caves and marine ecosystems.")
        ],
        "Shopping": [
            ("Artisan Craft Bazaar", "Dozens of open-air stalls selling local ceramics, textiles, and jewelry."),
            ("Grand Arcade Plaza", "Sophisticated multi-story shopping mall with designer boutiques."),
            ("Vintage Flea Alley", "Narrow corridors filled with antique vendors, books, and curiosities.")
        ],
        "Wildlife": [
            ("Safariland Eco-Park", "Drive-through animal park featuring native mammals and bird sanctuaries."),
            ("Marine Aquarium Center", "Vast underground tanks housing sharks, rays, and coral reefs."),
            ("Migratory Wetlands Lagoon", "Scenic boardwalks designed for birdwatching and photographing flora.")
        ]
    }
    
    selected_attractions = []
    chosen_interests = interests if interests else ["Culture", "Historical"]
    for interest in chosen_interests:
        if interest in interest_pool:
            for item in interest_pool[interest]:
                selected_attractions.append(item)
                
    general_pool = [
        ("Central Square & Plaza", "The historical town square and gathering place filled with cafes."),
        ("Scenic City Canal Cruise", "Boat tours cruising past historic bridges and architectural sites."),
        ("High Peak Observatory", "Astrophysics center with telescopes and panoramic platform overlooks."),
        ("Grand Library & Archives", "Beautiful 19th-century library building boasting frescoed ceilings.")
    ]
    for item in general_pool:
        selected_attractions.append(item)
        
    unique_items = []
    seen_names = set()
    for name, desc in selected_attractions:
        if name not in seen_names:
            seen_names.add(name)
            unique_items.append((name, desc))
            
    unique_items = unique_items[:30]
    
    final_attractions = []
    for idx, (name, desc) in enumerate(unique_items):
        offset_lat = (random.random() - 0.5) * 0.08
        offset_lon = (random.random() - 0.5) * 0.08
        final_attractions.append({
            "name": name,
            "description": desc,
            "rating": round(random.uniform(4.2, 4.9), 1),
            "lat": lat + offset_lat,
            "lng": lon + offset_lon
        })
        
    return final_attractions
