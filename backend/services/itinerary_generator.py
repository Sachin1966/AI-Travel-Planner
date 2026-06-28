import os
import json
import requests
import random
from dotenv import load_dotenv
from utils.helpers import geocode_destination

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def generate_full_itinerary(details: dict, hotels: list, attractions: list, weather: dict, budget_analysis: dict):
    """
    Orchestrates the prompt construction and sends it to local Ollama.
    Integrates the fetched hotels, attractions, weather, and budget data to create
    a highly coherent, unified travel plan.
    Falls back to a robust rule-based generator if Ollama is offline or errors.
    """
    dest = details["destination"]
    days = details["duration"]
    budget = details["budget"]
    party = details["party"]
    style = details["style"]
    interests = details["interests"]
    custom_prompt = details.get("custom_prompt", "")
    currency_symbol = details.get("currency_symbol", "$")
    currency_code = details.get("currency_code", "USD")
    
    # 1. Resolve coordinates
    lat, lon = geocode_destination(dest)
    if not lat:
        lat, lon = 48.8566, 2.3522 # Fallback Paris
        
    # Serialize context to inject into prompt
    hotels_context = json.dumps(hotels, indent=2)
    attractions_context = json.dumps(attractions, indent=2)
    
    system_instruction = f"""You are an elite travel planner AI. Generate a structured travel itinerary for a trip to {dest}.
You must incorporate the recommended hotels and attractions provided in the context below into the day-by-day activities.

CONTEXT DATA:
1. Recommended Hotels (include/refer to them for lodging details):
{hotels_context}

2. Recommended Attractions (incorporate these specific stops into the morning/afternoon/evening slots):
{attractions_context}

TRIP CRITERIA:
- Destination: {dest}
- Days: {days}
- Budget: {budget}
- Travelers: {party}
- Travel Style: {style}
- Interests: {", ".join(interests)}
- Custom Requests: {custom_prompt}

OUTPUT RULES:
1. You must output exactly {days} days.
2. Each day must contain exactly 3 activities (Morning, Afternoon, Evening).
3. The response MUST be a single raw JSON object that strictly adheres to the schema below.
4. Set the coordinates (lat, lng) for each activity. Use the coordinates from the Attractions context, or estimate them nearby.
5. Do NOT include markdown code blocks like ```json. Output only raw JSON.
6. All costs, activity pricing, and total budget estimates MUST be specified in the local currency of the destination, which is {currency_symbol} ({currency_code}).
   For example, use '{currency_symbol}X' where X is the value (e.g. '{currency_symbol}20' or '{currency_symbol}150').

JSON Schema:
{{
  "destination": "{dest}",
  "description": "2-sentence introduction of this trip for this traveler.",
  "total_budget_est": "Estimated total trip cost range (e.g. '{currency_symbol}1,500 - {currency_symbol}2,500' or equivalent)",
  "itinerary": [
    {{
      "day": 1,
      "theme": "Theme of Day 1",
      "activities": [
        {{
          "time": "Morning",
          "name": "Activity/Attraction Name",
          "description": "Engaging description mentioning what to see, what to do, or nearby restaurants.",
          "lat": 48.8530,
          "lng": 2.3499,
          "cost": "Cost estimate (e.g. Free or {currency_symbol}20)",
          "duration": "2 hours"
        }}
      ]
    }}
  ],
  "local_flavors": {{
    "cuisines": [
      {{"name": "Local Dish Name", "description": "Appetizing description"}}
    ],
    "beverages": [
      {{"name": "Local Drink Name", "description": "Appetizing description"}}
    ],
    "hotspots": "Neighborhoods or streets for great bistros, street food, and cafes"
  }},
  "travel_tips": [
    "Packing tip or local etiquette advice",
    "Safety or transit tip"
  ]
}}
"""

    # Call Ollama
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
                "temperature": 0.6
            }
        }
        res = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=15)
        if res.status_code == 200:
            result_json = res.json()
            raw_response = result_json.get("message", {}).get("content", "")
        else:
            print(f"Ollama server returned error code {res.status_code}. Falling back.")
    except Exception as e:
        print(f"Ollama failed to generate: {e}. Running local fallback engine.")
        
    # Parse and validate response
    if raw_response:
        try:
            # Clean markdown formatting if any
            cleaned_res = raw_response.strip()
            if cleaned_res.startswith("```"):
                cleaned_res = cleaned_res.split("\n", 1)[1] if "\n" in cleaned_res else cleaned_res
                if cleaned_res.endswith("```"):
                    cleaned_res = cleaned_res[:-3]
            cleaned_res = cleaned_res.strip()
            
            itinerary_data = json.loads(cleaned_res)
            
            # Populate extra fields from pre-fetched backend services to make a complete package
            itinerary_data["latitude"] = lat
            itinerary_data["longitude"] = lon
            itinerary_data["accommodations"] = hotels
            itinerary_data["weather"] = weather
            itinerary_data["budget_breakdown"] = budget_analysis.get("percentages")
            itinerary_data["budget_analysis"] = budget_analysis
            
            # Clean coordinates
            for d in itinerary_data.get("itinerary", []):
                for act in d.get("activities", []):
                    if "lat" not in act or not act["lat"] or "lng" not in act or not act["lng"]:
                        act["lat"] = lat + (random.random() - 0.5) * 0.05
                        act["lng"] = lon + (random.random() - 0.5) * 0.05
            return itinerary_data
        except Exception as parse_err:
            print(f"Failed to parse Ollama JSON response: {parse_err}. Falling back.")
            
    # 3. Running Heuristic Local Fallback
    return _generate_local_fallback(details, hotels, attractions, weather, budget_analysis, lat, lon)

MORNING_TEMPLATES = [
    ("{City} Central Square", "A morning stroll around the historic central square, admiring the architecture and enjoying a cup of coffee at a local cafe."),
    ("{City} Heritage Trail", "Walk along the historic neighborhood lanes, learning about the local heritage, old gates, and historic buildings."),
    ("{City} Botanical Garden", "A peaceful morning walk through the lush green gardens, viewing local flora and enjoying the fresh air."),
    ("{City} Artisan Market", "Browse local morning markets, observing local life, fresh produce, spices, and handmade crafts."),
    ("{City} Riverfront Walkway", "A scenic morning walk along the river bank or waterfront, catching the early views of the city skyline."),
    ("{City} Old Quarter", "Explore the winding streets of the old town, discovering hidden courtyards, historical markers, and vintage shops."),
    ("{City} Panoramic Viewpoint", "Head to a popular local hill or high tower to enjoy a stunning morning panorama of the entire city."),
    ("{City} Historic Library", "Visit the beautiful city archives or historic library building, viewing classic artwork and frescoed ceilings."),
    ("{City} Arts & Crafts Village", "Watch local craftsmen work on traditional pottery, weaving, and wood carvings in an interactive artisan village."),
    ("{City} Quiet Park", "Relax and unwind in a quiet neighborhood park, popular among locals for morning exercises and reading.")
]

AFTERNOON_TEMPLATES = [
    ("{City} Museum of History", "Spend the afternoon exploring the central history museum, viewing ancient artifacts and archaeological findings."),
    ("{City} Boulevard & Boutiques", "Leisurely shopping walk along the main boulevard, checking out local designer shops, bookstores, and cafes."),
    ("{City} Cultural Exhibition", "Visit the local cultural center to see contemporary art exhibitions, photography galleries, and craft displays."),
    ("{City} Food Bazaar & Tastings", "A guided culinary walk sampling regional street food, traditional sweets, and local delicacies."),
    ("{City} Lake Promenade", "A relaxing afternoon by the city lake, renting a paddleboat or walking along the shaded paths."),
    ("{City} Science & Space Center", "Explore the interactive science exhibits, planetarium shows, and modern tech displays."),
    ("{City} Historic Palace", "Tour the former royal residence or stately palace gardens, taking in the grand halls and elegant courtyards."),
    ("{City} Crafts & Souvenirs Market", "Find unique local souvenirs, handwoven textiles, and traditional jewelry in a bustling afternoon market plaza."),
    ("{City} Waterfront District", "Explore the modern dockyards and renovated harbor district, featuring chic cafes, art installations, and design shops."),
    ("{City} Cathedral & Cloisters", "Visit the city's main historical cathedral, admiring the stained-glass windows and tranquil stone cloisters.")
]

EVENING_TEMPLATES = [
    ("{City} Sunset Lookout", "Head to a scenic hilltop or bridge to watch the sunset over the city skyline and take stunning photos."),
    ("{City} Evening Food Street", "Explore the bustling night market or food street, tasting fresh local barbecue, snacks, and desserts."),
    ("{City} Theater & Performance Hall", "Catch a live traditional music show, dance performance, or local theater production at the cultural hall."),
    ("{City} Illuminated Old Town", "Take a night-time walking tour of the historic district, seeing the ancient buildings beautifully lit up."),
    ("{City} Rooftop Dining", "Enjoy a delicious dinner at a highly recommended local restaurant featuring panoramic city views under the stars."),
    ("{City} Lively Promenade", "Stroll along the main pedestrian street, filled with street performers, cafes, and a vibrant local crowd."),
    ("{City} Traditional Tea & Coffee House", "Wind down the day at a historic tea house or coffee salon, sampling regional beverages and desserts."),
    ("{City} Cozy Bistro Neighborhood", "Explore the narrow alleys of a trendy neighborhood, dinner shopping, and dining at a local family-run bistro."),
    ("{City} Music & Arts Cafe", "Enjoy an evening of live acoustic music, local poetry readings, or jazz in a cozy art cafe."),
    ("{City} Scenic Night Cruise", "Board a dinner cruise boat on the local river or bay, enjoying the city lights reflecting off the water.")
]

def _generate_local_fallback(details: dict, hotels: list, attractions: list, weather: dict, budget_analysis: dict, lat: float, lon: float):
    """
    Compiles a highly realistic fallback itinerary locally if Ollama is unavailable.
    """
    dest = details["destination"]
    days = details["duration"]
    budget = details["budget"]
    party = details["party"]
    style = details["style"]
    currency_symbol = details.get("currency_symbol", "$")
    
    # Select from pre-fetched attractions or create mock slots
    att_pool = attractions.copy()
    random.shuffle(att_pool)
    
    # Prepare template lists
    city_name = dest.split(",")[0].strip()
    m_temps = MORNING_TEMPLATES.copy()
    a_temps = AFTERNOON_TEMPLATES.copy()
    e_temps = EVENING_TEMPLATES.copy()
    random.shuffle(m_temps)
    random.shuffle(a_temps)
    random.shuffle(e_temps)
    
    itinerary = []
    times = ["Morning", "Afternoon", "Evening"]
    
    for day_num in range(1, days + 1):
        day_activities = []
        for time_slot in times:
            if att_pool:
                att = att_pool.pop()
                name = att.get("name")
                desc = f"Explore the scenic {name}. {att.get('description')}"
                act_lat = att.get("lat")
                act_lng = att.get("lng")
                rating = att.get("rating", 4.5)
            else:
                # Fallback to randomized non-repeating templates by time slot
                if time_slot == "Morning" and m_temps:
                    title_tpl, desc_tpl = m_temps.pop()
                elif time_slot == "Afternoon" and a_temps:
                    title_tpl, desc_tpl = a_temps.pop()
                elif time_slot == "Evening" and e_temps:
                    title_tpl, desc_tpl = e_temps.pop()
                else:
                    title_tpl, desc_tpl = ("{City} Local Explorer", "Leisurely walking exploration visiting historic buildings and local sights.")
                
                name = title_tpl.format(City=city_name)
                desc = desc_tpl.format(City=city_name)
                act_lat = lat + (random.random() - 0.5) * 0.05
                act_lng = lon + (random.random() - 0.5) * 0.05
                rating = 4.4
                
            day_activities.append({
                "time": time_slot,
                "name": name,
                "description": desc,
                "lat": act_lat,
                "lng": act_lng,
                "cost": "Free" if budget == "Budget" else (f"{currency_symbol}{random.randint(10, 35)}" if budget == "Mid-range" else f"{currency_symbol}{random.randint(60, 180)}"),
                "duration": "2.5 hours"
            })
            
        itinerary.append({
            "day": day_num,
            "theme": f"Exploring local landmarks and {style.lower()} activities",
            "activities": day_activities
        })
        
    # Local food recommendations
    dest_clean = dest.lower()
    if "goa" in dest_clean:
        cuisines = [
            {"name": "Fish Curry Rice", "description": "Goan staple featuring spiced kingfish curry served with hot steamed rice."},
            {"name": "Chicken Cafreal", "description": "Spicy chicken marinated in a thick coriander-green chili paste and shallow fried."},
            {"name": "Pork Vindaloo", "description": "Traditional fiery-hot Goan pork dish flavored with vinegar, garlic, and red chilies."},
            {"name": "Crab Xec Xec", "description": "Thick coconut-based curry loaded with roasted aromatic spices and fresh local crabs."}
        ]
        beverages = [
            {"name": "Feni", "description": "A legendary local spirit distilled from fermented cashew apples or coconut sap."},
            {"name": "Kokum Sherbet", "description": "Refreshing sweet-and-sour red beverage made from wild kokum berries."},
            {"name": "Sol Kadi", "description": "A pink digestive drink made from kokum and coconut milk with a hint of green chili."},
            {"name": "King's Beer", "description": "A popular local Goan premium pilsner lager found exclusively in beach shacks."}
        ]
        hotspots = "Explore the shacks along Anjuna, Baga, and Palolem for the freshest seafood and local curries."
    elif "paris" in dest_clean:
        cuisines = [
            {"name": "Duck Confit", "description": "Slow-cooked duck leg fried in its own fat until crispy, served with garlic potatoes."},
            {"name": "Croque Monsieur", "description": "Gourmet baked ham and cheese sandwich toasted with creamy béchamel sauce."},
            {"name": "Escargots de Bourgogne", "description": "Rich snails baked in their shells with chopped parsley and garlic butter."},
            {"name": "Soupe à l'Oignon", "description": "Classic French onion soup topped with caramelized onions and toasted gruyère cheese."}
        ]
        beverages = [
            {"name": "Bordeaux Wine", "description": "Classic rich French red wine paired perfectly with local steaks and cheeses."},
            {"name": "Chocolat Chaud", "description": "Thick, rich Parisian hot chocolate served with fresh whipped cream."},
            {"name": "French Kir", "description": "Sweet, refreshing aperitif made from dry white wine and blackcurrant liqueur."},
            {"name": "Café au Lait", "description": "Classic brewed coffee served with warm steamed milk in a wide bowl."}
        ]
        hotspots = "Le Marais and Saint-Germain-des-Prés are packed with historic bistros and artisanal bakeries."
    elif "tokyo" in dest_clean:
        cuisines = [
            {"name": "Sushi Moriawase", "description": "Chef's selection of fresh nigiri including tuna and sea bream served on seasoned rice."},
            {"name": "Tonkotsu Ramen", "description": "Rich 12-hour pork bone broth served with thin noodles, soft egg, and chashu pork."},
            {"name": "Tempura Moriawase", "description": "Crispy, light battered deep-fried seafood and seasonal vegetables."},
            {"name": "Yakitori Platter", "description": "Skewered chicken charcoal-grilled with savory tare glaze or sea salt."}
        ]
        beverages = [
            {"name": "Sake (Nihonshu)", "description": "Traditional Japanese brewed rice wine, served warm or chilled."},
            {"name": "Matcha Latte", "description": "Premium stone-ground green tea whisked with hot water and steamed milk."},
            {"name": "Shochu Highball", "description": "Refreshing carbonated cocktail made with distilled shochu and fresh lemon juice."},
            {"name": "Sencha Green Tea", "description": "Traditional steamed whole-leaf green tea with a grassy, sweet flavor."}
        ]
        hotspots = "Explore Memory Lane (Omoide Yokocho) in Shinjuku and Tsukiji Outer Market for fresh street bites."
    elif "new york" in dest_clean:
        cuisines = [
            {"name": "New York Slice", "description": "Thin-crust pizza folded in half, topped with rich tomato sauce and mozzarella."},
            {"name": "Pastrami on Rye", "description": "Warm, juicy cured pastrami piled high on rye bread with spicy brown mustard."},
            {"name": "Lox Bagel", "description": "Toasted bagel smeared with cream cheese, topped with smoked salmon, capers, and red onion."},
            {"name": "Manhattan Clam Chowder", "description": "Tomato-based savory red soup packed with fresh clams and stewed vegetables."}
        ]
        beverages = [
            {"name": "Manhattan Cocktail", "description": "Classic mix of rye whiskey, sweet vermouth, and bitters, with a cherry."},
            {"name": "Egg Cream", "description": "Traditional Brooklyn fountain drink with cold milk, seltzer, and chocolate syrup."},
            {"name": "New York Sour", "description": "Rye whiskey and lemon juice cocktail with a sweet red wine float on top."},
            {"name": "Brooklyn Craft IPA", "description": "Locally brewed aromatic pale ale with citrus and pine hop notes."}
        ]
        hotspots = "Chelsea Market and the DUMBO waterfront area in Brooklyn are packed with historical eateries."
    elif "london" in dest_clean:
        cuisines = [
            {"name": "Fish & Chips", "description": "Crispy beer-battered cod fillet served with thick-cut chips and mushy peas."},
            {"name": "Beef Wellington", "description": "Tender beef fillet wrapped in puff pastry with savory mushroom duxelles."},
            {"name": "Sunday Roast", "description": "Roasted beef served with fluffy Yorkshire pudding, roasted potatoes, and rich onion gravy."},
            {"name": "Chicken Tikka Masala", "description": "Roasted chunks of marinated chicken in a creamy, spiced orange-colored curry sauce."}
        ]
        beverages = [
            {"name": "Earl Grey Tea", "description": "Classic black tea blend flavored with aromatic oil of bergamot."},
            {"name": "Pimm's Cup", "description": "Refreshing gin-based punch mixed with lemonade, cucumber, mint, and fresh berries."},
            {"name": "Warm British Cider", "description": "Traditional fermented apple cider served warm with cinnamon spices."},
            {"name": "London Dry Gin & Tonic", "description": "Classic aromatic gin served with crisp tonic water and a wedge of lime."}
        ]
        hotspots = "Borough Market near London Bridge and Covent Garden are ideal for street food and historic pubs."
    elif "rome" in dest_clean:
        cuisines = [
            {"name": "Spaghetti alla Carbonara", "description": "Roman pasta made with egg yolk, pecorino romano, guanciale, and black pepper."},
            {"name": "Cacio e Pepe", "description": "Simple yet delicious pasta combining pecorino romano and cracked black pepper."},
            {"name": "Saltimbocca alla Romana", "description": "Tender veal cutlets lined with prosciutto and sage, pan-fried in white wine."},
            {"name": "Suppli al Telefono", "description": "Crispy fried rice croquettes filled with beef ragù and melted mozzarella."}
        ]
        beverages = [
            {"name": "Limoncello", "description": "Sweet, chilled lemon liqueur served as a digestif after dinner."},
            {"name": "Espresso Romano", "description": "Rich concentrated shot of espresso served with a twist of fresh lemon."},
            {"name": "Aperol Spritz", "description": "Refreshing prosecco cocktail mixed with Aperol bitters, soda water, and a slice of orange."},
            {"name": "Frascati Superiore", "description": "Crisp, dry white wine from the volcanic hills surrounding Rome."}
        ]
        hotspots = "Trastevere and Testaccio neighborhoods host the most authentic Roman osterias and trattorias."
    elif "mumbai" in dest_clean:
        cuisines = [
            {"name": "Vada Pav", "description": "The signature spicy potato dumpling burger served in a soft bun with chutneys."},
            {"name": "Pav Bhaji", "description": "Thick, spicy mashed vegetable curry served with toasted, butter-soaked bread rolls."},
            {"name": "Bhel Puri", "description": "Tangy, sweet street snack made with puffed rice, vegetables, and tamarind chutney."},
            {"name": "Bombil Fry", "description": "Crispy rava-fried Bombay Duck fish, a beloved coastal delicacy."}
        ]
        beverages = [
            {"name": "Cutting Chai", "description": "Strongly brewed cardamom-ginger sweet tea served with milk."},
            {"name": "Kokum Sherbet", "description": "Refreshing sweet-and-sour pink summer cooler made from wild kokum berries."},
            {"name": "Mango Lassi", "description": "Creamy yogurt beverage blended with sweet, ripe Alphonso mangoes."},
            {"name": "Neera", "description": "Sweet, refreshing palm nectar tapped fresh from coconut trees in the mornings."}
        ]
        hotspots = "Girgaon Chowpatty beach for chaat stalls and the alleys of Mohammad Ali Road for desserts."
    elif "sydney" in dest_clean:
        cuisines = [
            {"name": "Seared Barramundi", "description": "Fresh Australian barramundi sea bass fillet seared and served with lemon butter."},
            {"name": "Aussie Meat Pie", "description": "Crispy pastry crust filled with minced beef gravy and topped with tomato sauce."},
            {"name": "Moreton Bay Bugs", "description": "Succulent local flathead lobsters grilled with garlic and herb butter."},
            {"name": "Pavlova", "description": "Crisp meringue dessert topped with whipped cream and fresh passion fruit, kiwi, and berries."}
        ]
        beverages = [
            {"name": "Flat White", "description": "Double shot of espresso topped with velvety microfoamed hot milk."},
            {"name": "Ginger Beer", "description": "Sparkling non-alcoholic ginger cooler brewed with Queensland ginger."},
            {"name": "Hunter Valley Semillon", "description": "Crisp, citrusy local white wine unique to the region."},
            {"name": "Lemon, Lime and Bitters", "description": "Popular refreshing pub beverage made with lemonade, lime, and Angostura bitters."}
        ]
        hotspots = "Sydney Fish Market and the bohemian cafes along King Street in Newtown."
    elif "berlin" in dest_clean:
        cuisines = [
            {"name": "Currywurst", "description": "Fried pork sausage sliced and covered with spiced curried ketchup, served with fries."},
            {"name": "Wiener Schnitzel", "description": "Pan-fried breaded veal cutlet served with German potato salad."},
            {"name": "Eisbein", "description": "Traditional tender ham hock boiled and served with sauerkraut and pea puree."},
            {"name": "Döner Kebab", "description": "Crispy flatbread stuffed with shaved spit-roasted meat, salad, and garlic herb sauce."}
        ]
        beverages = [
            {"name": "Berliner Weisse", "description": "Sour wheat beer flavored with sweet raspberry or woodruff syrup."},
            {"name": "Club-Mate", "description": "Popular carbonated mate-extract beverage packed with natural caffeine."},
            {"name": "Radler", "description": "Refreshing blend of light German Pilsner beer and sparkling lemonade."},
            {"name": "Schnapps", "description": "Potent fruit-flavored clear spirit served ice-cold as a digestive shot."}
        ]
        hotspots = "Kreuzberg and Prenzlauer Berg are loaded with beer gardens and currywurst stands."
    elif "singapore" in dest_clean:
        cuisines = [
            {"name": "Hainanese Chicken Rice", "description": "Poached chicken served with fragrant seasoned rice, chili, and ginger."},
            {"name": "Chili Crab", "description": "Stir-fried mud crab cooked in a thick, sweet, and savory egg-chili sauce."},
            {"name": "Laksa", "description": "Spicy coconut curry noodle soup topped with shrimp, fish cakes, and cockles."},
            {"name": "Roti Prata", "description": "Crispy, flaky pan-fried flatbread served with savory mutton or vegetable dal curry."}
        ]
        beverages = [
            {"name": "Singapore Sling", "description": "Famous gin-based cocktail mixed with cherry brandy, Cointreau, and pineapple."},
            {"name": "Teh Tarik", "description": "Sweet, frothy pulled tea mixed with condensed milk and poured between cups."},
            {"name": "Milo Dinosaur", "description": "Cold iced chocolate malt drink topped with a generous heap of raw Milo powder."},
            {"name": "Tiger Beer", "description": "Singapore's iconic crisp, refreshing pale lager."}
        ]
        hotspots = "Lau Pa Sat and Maxwell Food Centre are elite historic open-air hawker markets."
    elif "dubai" in dest_clean:
        cuisines = [
            {"name": "Chicken Shawarma", "description": "Spit-roasted chicken wrapped in flatbread with garlic sauce and pickles."},
            {"name": "Lamb Mandi", "description": "Slow-cooked spiced lamb served over fragrant long-grain basmati rice."},
            {"name": "Luqaimat", "description": "Sweet, crunchy deep-fried dough balls drizzled with warm date syrup and sesame seeds."},
            {"name": "Grilled Hammour", "description": "Locally caught grouper seasoned with Middle Eastern spices and grilled over charcoal."}
        ]
        beverages = [
            {"name": "Arabic Coffee (Gahwa)", "description": "Spiced cardamom coffee brewed in a dallah pot and served with dates."},
            {"name": "Jallab", "description": "Sweet syrup made from dates, grape molasses, and rose water, topped with pine nuts."},
            {"name": "Laban", "description": "Refreshing, cold salted buttermilk beverage perfect for the warm climate."},
            {"name": "Lemon Mint Cooler", "description": "Blended fresh mint leaves, lemon juice, ice, and sweet syrup."}
        ]
        hotspots = "The Al Fahidi historic district and the lively street stalls in Deira."
    elif "cairo" in dest_clean:
        cuisines = [
            {"name": "Koshary", "description": "National dish mixing rice, lentils, macaroni, chickpeas, tomato sauce, and crispy onions."},
            {"name": "Ta'ameya", "description": "Egyptian falafel made from crushed fava beans and fresh herbs, served in pita."},
            {"name": "Ful Medames", "description": "Slow-cooked fava beans seasoned with olive oil, cumin, garlic, and fresh lemon juice."},
            {"name": "Mahshi", "description": "Vine leaves or vegetables stuffed with a spiced rice, herb, and tomato mixture."}
        ]
        beverages = [
            {"name": "Karkadeh", "description": "Sweet, tart crimson herbal tea brewed from dried hibiscus flowers."},
            {"name": "Mint Tea", "description": "Strongly brewed Egyptian black tea packed with fresh spearmint leaves."},
            {"name": "Sugarcane Juice (Asab)", "description": "Freshly squeezed sweet and cold raw sugarcane stalk juice."},
            {"name": "Sahlab", "description": "Warm, creamy winter drink made from orchid root powder, topped with nuts and cinnamon."}
        ]
        hotspots = "The historic El Fishawy Cafe in Khan el-Khalili and Zamalek island for modern dining."
    elif any(k in dest_clean for k in ["india", "tamil nadu", "chennai", "ooty", "kodaikanal", "madurai", "rameshwaram", "mahabalipuram", "kanyakumari", "thanjavur", "coimbatore", "kanchipuram"]):
        cuisines = [
            {"name": "Masala Dosa & Sambar", "description": "Crispy rice crepe filled with spiced potato mash, served with warm lentil stew and coconut chutney."},
            {"name": "Chettinad Pepper Chicken", "description": "Famous spicy chicken dish cooked with fresh ground spices, black pepper, and curry leaves."},
            {"name": "Madurai Bun Parotta", "description": "Layered, flaky, soft flatbread shaped like a bun and served with spicy mutton or chicken salna."},
            {"name": "Thalassery Biryani", "description": "Fragrant, spiced rice dish cooked with tender meat, ghee, and whole spices."}
        ]
        beverages = [
            {"name": "South Indian Filter Coffee", "description": "Rich chicory-blended coffee frothed with hot milk in a traditional brass dabarah."},
            {"name": "Madurai Jigarthanda", "description": "Sweet, cold dessert beverage containing almond gum, milk, sarsaparilla, and ice cream."},
            {"name": "Panakam", "description": "Traditional sweet drink made from jaggery, ginger powder, cardamom, and fresh lemon juice."},
            {"name": "Nannari Sarbath", "description": "Refreshing cold summer drink flavored with sweet sarsaparilla root syrup and fresh lime."}
        ]
        hotspots = "Famous local eateries like Saravana Bhavan, Murugan Idli Shop, and traditional Chettinad mess halls."
    elif any(k in dest_clean for k in ["italy", "venice", "florence", "milan"]):
        cuisines = [
            {"name": "Margherita Pizza", "description": "Classic Neapolitan pizza topped with san marzano tomatoes, fresh mozzarella, and basil."},
            {"name": "Lasagna al Forno", "description": "Baked flat pasta sheets layered with rich bolognese ragu, creamy béchamel, and parmigiano."},
            {"name": "Risotto alla Milanese", "description": "Creamy arborio rice cooked with saffron, butter, beef marrow, and parmigiano."},
            {"name": "Bistecca alla Fiorentina", "description": "Thick-cut T-bone steak from Chianina beef, grilled rare over oak embers."}
        ]
        beverages = [
            {"name": "Espresso", "description": "Strong, rich shot of concentrated espresso coffee served in a warm demitasse."},
            {"name": "Chianti Classico", "description": "Ruby red Italian dry wine from the Tuscany region, pairing beautifully with pasta."},
            {"name": "Campari Soda", "description": "Vibrant red bittersweet herbal liqueur mixed with club soda."},
            {"name": "Negroni", "description": "Classic Italian cocktail of gin, vermouth rouge, and Campari garnished with orange peel."}
        ]
        hotspots = "Look for family-run Osterias and Trattorias tucked away from the main tourist squares."
    elif any(k in dest_clean for k in ["spain", "barcelona", "madrid", "seville"]):
        cuisines = [
            {"name": "Seafood Paella", "description": "Spanish saffron rice cooked in a shallow pan with shrimp, mussels, squid, and herbs."},
            {"name": "Patatas Bravas", "description": "Crispy cubed potatoes served with warm, spicy tomato sauce and garlic aioli."},
            {"name": "Jamón Ibérico", "description": "Premium cured ham made from free-range acorn-fed Iberian pigs, sliced paper-thin."},
            {"name": "Tortilla de Patatas", "description": "Traditional Spanish omelet cooked with thick layers of eggs, potatoes, and olive oil."}
        ]
        beverages = [
            {"name": "Sangria", "description": "Sweet, refreshing punch made of red wine, chopped fruits, orange juice, and brandy."},
            {"name": "Cortado", "description": "Rich espresso cut with a small amount of warm milk to reduce acidity."},
            {"name": "Clara de Limón", "description": "Refreshing summer drink mixing Spanish lager beer with carbonated lemonade."},
            {"name": "Horchata de Chufa", "description": "Creamy, sweet milk-like drink squeezed from tiger nuts, served ice-cold."}
        ]
        hotspots = "Explore local Tapas bars along the historic quarters and central food halls."
    elif any(k in dest_clean for k in ["china", "beijing", "shanghai"]):
        cuisines = [
            {"name": "Peking Duck", "description": "Crispy thin-skinned roasted duck served with sweet bean sauce and cucumber wraps."},
            {"name": "Xiao Long Bao", "description": "Delicate steamed soup dumplings filled with juicy pork and hot broth."},
            {"name": "Kung Pao Chicken", "description": "Stir-fried diced chicken with peanuts, vegetables, and chili peppers."},
            {"name": "Mapo Tofu", "description": "Spicy, numbing Sichuan dish featuring tofu set in a minced beef and chili bean sauce."}
        ]
        beverages = [
            {"name": "Jasmine Tea", "description": "Fragrant green tea scented with fresh jasmine blossoms, aiding digestion."},
            {"name": "Tsingtao Beer", "description": "Crisp, refreshing German-style pilsner brewed in Qingdao."},
            {"name": "Baijiu", "description": "Traditional strong distilled Chinese grain liquor."},
            {"name": "Plum Syrup Drink (Suanmeitang)", "description": "Traditional sweet and sour beverage made from smoked plums and sweet osmanthus."}
        ]
        hotspots = "The bustling evening night markets and historic lanes (Hutongs) for street food stalls."
    else:
        cuisines = [
            {"name": "Regional Platter", "description": "A delightful plate featuring regional cheeses, slow-cooked meats, and local vegetables."},
            {"name": "Local Savory Pastry", "description": "Freshly baked pie filled with spiced local herbs and roasted beef."},
            {"name": "Grilled Catch of the Day", "description": "Freshly grilled local fish seasoned with hand-picked seasonal herbs and lemon juice."},
            {"name": "Baked Forest Berry Tart", "description": "Crispy butter crust filled with seasonal sweet wild berries and whipped cream."}
        ]
        beverages = [
            {"name": "Craft Brew", "description": "A popular regional beverage brewed with local mountain spring water."},
            {"name": "Herbal Tea", "description": "Warm, comforting tea infused with native wildflower honey."},
            {"name": "Mulled Cider", "description": "Warm spiced apple juice infused with local cinnamon, cloves, and orange slices."},
            {"name": "Wildberry Cooler", "description": "Iced infusion of crushed fresh forest berries and sparkling mineral water."}
        ]
        hotspots = "The Old Market Street and Riverside district for the best local cafes, bakeries, and food stalls."

    return {
        "destination": dest,
        "description": f"An immersive travel experience in {dest} tailored for {party.lower()} travelers. Your itinerary centers on a {style.lower()} travel style.",
        "latitude": lat,
        "longitude": lon,
        "total_budget_est": budget_analysis.get("total_budget"),
        "itinerary": itinerary,
        "accommodations": hotels,
        "weather": weather,
        "budget_breakdown": budget_analysis.get("percentages"),
        "budget_analysis": budget_analysis,
        "local_flavors": {
            "cuisines": cuisines,
            "beverages": beverages,
            "hotspots": hotspots
        },
        "travel_tips": [
            "Keep digital copies of all identification and travel insurance on your phone.",
            "Use local public transit cards to save money on daily commutes.",
            "Pack versatile layers as local weather can shift throughout the day.",
            "Learn a few key local phrases like 'Thank you' and 'Hello' to connect with locals."
        ]
    }
