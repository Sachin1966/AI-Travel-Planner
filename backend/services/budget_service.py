def analyze_budget(budget_level: str, total_budget: str, currency_symbol: str = "$"):
    """
    Computes a tailored budget breakdown and provides strategic savings suggestions
    based on the budget tier and travel criteria.
    """
    # Parse numeric budget if possible, else default
    try:
        clean_budget = total_budget.replace("₹", "").replace("$", "").replace("€", "").replace("£", "").replace("¥", "").replace(",", "").strip()
        if "-" in clean_budget:
            # Average of range
            parts = clean_budget.split("-")
            budget_val = (float(parts[0].strip()) + float(parts[1].strip())) / 2
        else:
            budget_val = float(clean_budget)
    except Exception:
        budget_val = 1500.0  # Default fallback representation
        
    # Breakdown allocations based on budget level
    if budget_level == "Budget":
        breakdown = {
            "Accommodations": 35,
            "Food & Drinks": 30,
            "Transport": 15,
            "Activities": 12,
            "Miscellaneous": 8
        }
        savings_tips = [
            "Use public transit (metros, buses) or walk instead of hiring private taxis.",
            "Eat at local street food stalls and residential neighborhood bistros rather than tourist squares.",
            "Look for free walking tours and search for museum days with free entrance.",
            "Stay in high-rated hostels or cozy guesthouse homestays to cut lodging expenses."
        ]
    elif budget_level == "Luxury":
        breakdown = {
            "Accommodations": 50,
            "Food & Drinks": 25,
            "Transport": 10,
            "Activities": 10,
            "Miscellaneous": 5
        }
        savings_tips = [
            "Book luxury hotel packages directly to get complimentary spa or dining credits.",
            "Hire a dedicated private chauffeur for full-day excursions rather than scheduling individual luxury transfers.",
            "Opt for multi-course chef tasting menus which offer better value than ordering high-end dishes à la carte.",
            "Leverage premium credit card concierge services for exclusive booking discounts and free lounge entries."
        ]
    else:  # Mid-range
        breakdown = {
            "Accommodations": 42,
            "Food & Drinks": 28,
            "Transport": 12,
            "Activities": 12,
            "Miscellaneous": 6
        }
        savings_tips = [
            "Look for boutique hotels that include hot breakfasts to eliminate one daily meal cost.",
            "Purchase bundle passes or city cards (e.g. Paris Museum Pass) for discounted entry to multiple sites.",
            "Use regional trains or shared airport shuttle rides instead of private taxis.",
            "Mix mid-range dining with occasional street food snacks to stretch your food budget."
        ]

    # Calculate actual estimated currency values
    monetary_breakdown = {}
    for cat, pct in breakdown.items():
        monetary_breakdown[cat] = f"{currency_symbol}{round((pct / 100.0) * budget_val, 2)}"
        
    return {
        "budget_level": budget_level,
        "total_budget": total_budget,
        "percentages": breakdown,
        "amounts": monetary_breakdown,
        "savings_suggestions": savings_tips
    }
