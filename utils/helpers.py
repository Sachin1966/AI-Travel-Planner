import requests

HEADERS = {"User-Agent": "ExpeditionAITravelPlanner/1.0 (contact: asach@github.com) Python-Requests/2.31"}

NOMINATIM_CACHE = {}

def nominatim_request(url: str) -> list | dict | None:
    if url in NOMINATIM_CACHE:
        return NOMINATIM_CACHE[url]
    try:
        res = requests.get(url, headers=HEADERS, timeout=3)
        if res.status_code == 200:
            data = res.json()
            NOMINATIM_CACHE[url] = data
            return data
        elif res.status_code == 429:
            print("Nominatim rate limited (429).")
        else:
            print(f"Nominatim returned status {res.status_code}")
    except Exception as e:
        print(f"Nominatim request error: {e}")
    return None

CURRENCY_MAP = {
    "us": ("$", "USD"),
    "in": ("₹", "INR"),
    "gb": ("£", "GBP"),
    "jp": ("¥", "JPY"),
    "cn": ("¥", "CNY"),
    "ca": ("C$", "CAD"),
    "au": ("A$", "AUD"),
    "ch": ("CHF", "CHF"),
    "sg": ("S$", "SGD"),
    "ae": ("AED", "AED"),
    "th": ("฿", "THB"),
    "my": ("RM", "MYR"),
    "id": ("Rp", "IDR"),
    "vn": ("₫", "VND"),
    "ph": ("₱", "PHP"),
    "kr": ("₩", "KRW"),
    "hk": ("HK$", "HKD"),
    "nz": ("NZ$", "NZD"),
    "br": ("R$", "BRL"),
    "mx": ("Mex$", "MXN"),
    "za": ("R", "ZAR"),
    "tr": ("₺", "TRY"),
    "ru": ("₽", "RUB"),
    "sa": ("SR", "SAR"),
    "eg": ("E£", "EGP"),
    "se": ("kr", "SEK"),
    "no": ("kr", "NOK"),
    "dk": ("kr", "DKK"),
    "pl": ("zł", "PLN"),
    # Eurozone
    "fr": ("€", "EUR"),
    "de": ("€", "EUR"),
    "es": ("€", "EUR"),
    "it": ("€", "EUR"),
    "nl": ("€", "EUR"),
    "be": ("€", "EUR"),
    "at": ("€", "EUR"),
    "fi": ("€", "EUR"),
    "gr": ("€", "EUR"),
    "ie": ("€", "EUR"),
    "pt": ("€", "EUR"),
    "ee": ("€", "EUR"),
    "lv": ("€", "EUR"),
    "lt": ("€", "EUR"),
    "sk": ("€", "EUR"),
    "si": ("€", "EUR"),
    "hr": ("€", "EUR"),
    "cy": ("€", "EUR"),
    "mt": ("€", "EUR"),
}

def geocode_destination(destination_name: str):
    """
    Geocodes a destination name to (latitude, longitude) using OpenStreetMap Nominatim.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(destination_name)}&format=json&limit=1&addressdetails=1"
        data = nominatim_request(url)
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Geocoding helper error: {e}")
    return None, None

def get_currency_by_text(destination_name: str) -> tuple[str, str]:
    """
    Fallback text parser to determine currency from destination string.
    """
    dest_lower = destination_name.lower()
    if any(k in dest_lower for k in ["india", "goa", "delhi", "mumbai", "bengaluru", "bangalore", "hyderabad", "chennai", "kolkata", "jaipur", "kerala", "agra"]):
        return "₹", "INR"
    if any(k in dest_lower for k in ["france", "paris", "germany", "berlin", "munich", "spain", "madrid", "barcelona", "italy", "rome", "milan", "venice", "florence", "amsterdam", "netherlands", "belgium", "brussels", "austria", "vienna", "greece", "athens", "portugal", "lisbon", "ireland", "dublin"]):
        return "€", "EUR"
    if any(k in dest_lower for k in ["uk", "united kingdom", "london", "manchester", "scotland", "edinburgh", "england"]):
        return "£", "GBP"
    if any(k in dest_lower for k in ["japan", "tokyo", "kyoto", "osaka"]):
        return "¥", "JPY"
    if any(k in dest_lower for k in ["china", "beijing", "shanghai"]):
        return "¥", "CNY"
    if any(k in dest_lower for k in ["canada", "toronto", "vancouver", "montreal"]):
        return "C$", "CAD"
    if any(k in dest_lower for k in ["australia", "sydney", "melbourne", "brisbane"]):
        return "A$", "AUD"
    if any(k in dest_lower for k in ["switzerland", "zurich", "geneva"]):
        return "CHF", "CHF"
    if any(k in dest_lower for k in ["singapore"]):
        return "S$", "SGD"
    if any(k in dest_lower for k in ["thailand", "bangkok", "phuket", "pattaya"]):
        return "฿", "THB"
    if any(k in dest_lower for k in ["malaysia", "kuala lumpur"]):
        return "RM", "MYR"
    if any(k in dest_lower for k in ["indonesia", "bali", "jakarta"]):
        return "Rp", "IDR"
    if any(k in dest_lower for k in ["vietnam", "hanoi", "ho chi minh"]):
        return "₫", "VND"
    if any(k in dest_lower for k in ["philippines", "manila"]):
        return "₱", "PHP"
    if any(k in dest_lower for k in ["korea", "seoul"]):
        return "₩", "KRW"
    if any(k in dest_lower for k in ["hong kong"]):
        return "HK$", "HKD"
    if any(k in dest_lower for k in ["new zealand", "auckland"]):
        return "NZ$", "NZD"
    if any(k in dest_lower for k in ["brazil", "rio", "sao paulo"]):
        return "R$", "BRL"
    if any(k in dest_lower for k in ["mexico", "cancun"]):
        return "Mex$", "MXN"
    if any(k in dest_lower for k in ["south africa", "cape town", "johannesburg"]):
        return "R", "ZAR"
    if any(k in dest_lower for k in ["turkey", "istanbul", "ankara"]):
        return "₺", "TRY"
    if any(k in dest_lower for k in ["dubai", "uae", "abu dhabi", "emirates"]):
        return "AED", "AED"
    
    return "$", "USD"

def get_destination_currency(destination_name: str) -> tuple[str, str]:
    """
    Resolves the currency symbol and code using Nominatim with address details,
    falling back to a text parser.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(destination_name)}&format=json&limit=1&addressdetails=1"
        data = nominatim_request(url)
        if data and "address" in data[0]:
            addr = data[0]["address"]
            cc = addr.get("country_code", "").lower()
            if cc in CURRENCY_MAP:
                return CURRENCY_MAP[cc]
    except Exception as e:
        print(f"Currency lookup helper error: {e}")
    
    return get_currency_by_text(destination_name)

def parse_currency_amount(budget_str: str) -> tuple[float, str]:
    """
    Parses a budget string like 'INR 30000' or '$1500' into (value, currency_code).
    """
    cleaned = budget_str.upper().strip()
    code = "USD"
    if "INR" in cleaned or "₹" in cleaned or "RS" in cleaned:
        code = "INR"
    elif "EUR" in cleaned or "€" in cleaned:
        code = "EUR"
    elif "GBP" in cleaned or "£" in cleaned:
        code = "GBP"
    elif "JPY" in cleaned or "¥" in cleaned:
        code = "CNY" if "CNY" in cleaned else "JPY"
    elif "CAD" in cleaned or "C$" in cleaned:
        code = "CAD"
    elif "AUD" in cleaned or "A$" in cleaned:
        code = "AUD"
    elif "CHF" in cleaned:
        code = "CHF"
    elif "SGD" in cleaned or "S$" in cleaned:
        code = "SGD"
    elif "THB" in cleaned or "฿" in cleaned:
        code = "THB"
    elif "MYR" in cleaned or "RM" in cleaned:
        code = "MYR"
    elif "IDR" in cleaned or "RP" in cleaned:
        code = "IDR"
    elif "VND" in cleaned or "₫" in cleaned:
        code = "VND"
    elif "PHP" in cleaned or "₱" in cleaned:
        code = "PHP"
    elif "KRW" in cleaned or "₩" in cleaned:
        code = "KRW"
    elif "HKD" in cleaned or "HK$" in cleaned:
        code = "HKD"
    elif "NZD" in cleaned or "NZ$" in cleaned:
        code = "NZD"
    elif "BRL" in cleaned or "R$" in cleaned:
        code = "BRL"
    elif "MXN" in cleaned or "MEX$" in cleaned:
        code = "MXN"
    elif "ZAR" in cleaned or "R" in cleaned:
        if "ZAR" in cleaned:
            code = "ZAR"
    elif "TRY" in cleaned or "₺" in cleaned:
        code = "TRY"
    elif "AED" in cleaned:
        code = "AED"
        
    # Extract digits and decimal point
    digits = []
    has_dot = False
    for char in budget_str:
        if char.isdigit():
            digits.append(char)
        elif char == '.' and not has_dot:
            digits.append(char)
            has_dot = True
            
    val = 1500.0
    if digits:
        try:
            val = float("".join(digits))
        except ValueError:
            pass
            
    return val, code

def convert_currency(value: float, from_code: str, to_code: str) -> float:
    """
    Converts a value between currencies using hardcoded rates relative to USD.
    """
    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "INR": 83.5,
        "GBP": 0.79,
        "JPY": 158.0,
        "CNY": 7.25,
        "CAD": 1.37,
        "AUD": 1.50,
        "CHF": 0.89,
        "SGD": 1.35,
        "THB": 36.7,
        "MYR": 4.71,
        "IDR": 16400.0,
        "VND": 25400.0,
        "PHP": 58.7,
        "KRW": 1390.0,
        "HKD": 7.8,
        "NZD": 1.63,
        "BRL": 5.4,
        "MXN": 18.0,
        "ZAR": 18.2,
        "TRY": 32.8,
        "AED": 3.67,
    }
    f_code = from_code.upper().strip()
    t_code = to_code.upper().strip()
    
    if f_code == t_code:
        return value
        
    if f_code in rates and t_code in rates:
        val_usd = value / rates[f_code]
        return val_usd * rates[t_code]
        
    return value
