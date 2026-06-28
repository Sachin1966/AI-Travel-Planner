import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def sanitize_text_for_pdf(text: str) -> str:
    """
    Safely sanitizes text by replacing unicode symbols to prevent ReportLab encoding crashes.
    """
    if not text:
        return ""
    return (text.replace("₹", "INR ")
                .replace("$", "USD ")
                .replace("€", "EUR ")
                .replace("£", "GBP ")
                .replace("¥", "JPY ")
                .replace("฿", "THB ")
                .replace("₫", "VND ")
                .replace("₱", "PHP ")
                .replace("₩", "KRW ")
                .replace("₺", "TRY ")
                .replace("•", "-"))

def generate_pdf_itinerary(itinerary_data: dict) -> io.BytesIO:
    """
    Compiles a highly professional, multi-page travel itinerary PDF using ReportLab
    and returns the binary file as a BytesIO stream.
    """
    buffer = io.BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles matching Indigo theme
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=colors.HexColor('#4F46E5'),
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=16,
        leading=22,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        textColor=colors.HexColor('#1E1B4B'),
        spaceBefore=20,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SubSectionHeading',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#4F46E5'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8
    )
    
    meta_label_style = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#4F46E5')
    )
    
    meta_val_style = ParagraphStyle(
        'MetaValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.HexColor('#111827')
    )

    story = []
    
    # ================= PAGE 1: COVER PAGE =================
    story.append(Spacer(1, 150))
    story.append(Paragraph("EXPEDITION PLANNER", title_style))
    story.append(Spacer(1, 15))
    dest_name = sanitize_text_for_pdf(itinerary_data.get("destination", "Your Destination"))
    story.append(Paragraph(f"Bespoke Itinerary for {dest_name}", subtitle_style))
    story.append(Spacer(1, 40))
    
    # Metadata Block
    budget_level = itinerary_data.get("budget_analysis", {}).get("budget_level", "Mid-range")
    total_est = sanitize_text_for_pdf(itinerary_data.get("total_budget_est", "$1,500 - $2,500"))
    
    meta_data = [
        [Paragraph("Destination:", meta_label_style), Paragraph(dest_name, meta_val_style)],
        [Paragraph("Est. Budget:", meta_label_style), Paragraph(total_est, meta_val_style)],
        [Paragraph("Budget Tier:", meta_label_style), Paragraph(budget_level, meta_val_style)],
        [Paragraph("Date Generated:", meta_label_style), Paragraph(str(datetime.datetime.now().strftime("%Y-%m-%d")), meta_val_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[150, 250])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    
    story.append(meta_table)
    story.append(PageBreak())
    
    # ================= PAGE 2: TRIP SUMMARY & WEATHER =================
    story.append(Paragraph("Trip Summary", h1_style))
    desc_txt = sanitize_text_for_pdf(itinerary_data.get("description", "Enjoy your trip!"))
    story.append(Paragraph(desc_txt, body_style))
    story.append(Spacer(1, 15))
    
    # Weather
    weather = itinerary_data.get("weather")
    if weather:
        story.append(Paragraph("Weather Forecast & Travel Advice", h2_style))
        weather_desc = sanitize_text_for_pdf(weather.get("description", "Sunny"))
        temp = weather.get("temp", 25)
        advice = sanitize_text_for_pdf(weather.get("advice", ""))
        
        weather_txt = f"Current Condition: {weather_desc} | Temp: {temp}C. <br/><b>Advice:</b> {advice}"
        story.append(Paragraph(weather_txt, body_style))
        story.append(Spacer(1, 15))
        
    # Budget Breakdown
    story.append(Paragraph("Budget Allocation Breakdown", h2_style))
    breakdown_data = [["Expense Category", "Allocation Percentage"]]
    budget_breakdown = itinerary_data.get("budget_breakdown", {})
    if budget_breakdown:
        for cat, val in budget_breakdown.items():
            breakdown_data.append([cat, f"{val}%"])
            
        budget_table = Table(breakdown_data, colWidths=[200, 100])
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ]))
        story.append(budget_table)
        
    story.append(PageBreak())
    
    # ================= PAGE 3: DAY-BY-DAY SCHEDULE =================
    story.append(Paragraph("Day-by-Day Timeline", h1_style))
    
    itinerary_list = itinerary_data.get("itinerary", [])
    for d_idx, day_plan in enumerate(itinerary_list):
        day_num = day_plan.get("day", d_idx + 1)
        day_theme = sanitize_text_for_pdf(day_plan.get("theme", "Explore"))
        
        story.append(Paragraph(f"Day {day_num}: {day_theme}", h2_style))
        
        day_acts = [["Time", "Activity", "Est. Cost", "Duration"]]
        for act in day_plan.get("activities", []):
            time_slot = act.get("time", "Morning")
            name = sanitize_text_for_pdf(act.get("name", "Attraction"))
            cost = sanitize_text_for_pdf(act.get("cost", "Free"))
            dur = sanitize_text_for_pdf(act.get("duration", "2 hours"))
            
            day_acts.append([time_slot, name, cost, dur])
            
        act_table = Table(day_acts, colWidths=[70, 200, 80, 80])
        act_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1F2937')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        
        story.append(act_table)
        story.append(Spacer(1, 15))
        
    story.append(PageBreak())
    
    # ================= PAGE 4: HOTELS & LOCAL FLAVORS =================
    story.append(Paragraph("Lodging & Accommodations", h1_style))
    hotels = itinerary_data.get("accommodations", [])
    for hotel in hotels:
        h_name = sanitize_text_for_pdf(hotel.get("name", "Hotel"))
        h_type = hotel.get("type", "Mid-range")
        h_price = sanitize_text_for_pdf(hotel.get("approx_price", hotel.get("price_level", "$$")))
        h_desc = sanitize_text_for_pdf(hotel.get("description", hotel.get("address", "")))
        h_rating = hotel.get("rating", 4.0)
        
        story.append(Paragraph(f"<b>{h_name}</b> ({h_type} • {h_rating} Stars)", body_style))
        story.append(Paragraph(f"Price: {h_price} | {h_desc}", body_style))
        story.append(Spacer(1, 8))
        
    story.append(Spacer(1, 15))
    story.append(Paragraph("Local Flavors Guide", h1_style))
    flavors = itinerary_data.get("local_flavors", {})
    if flavors:
        story.append(Paragraph("<b>Must-Try Local Foods:</b>", body_style))
        for dish in flavors.get("cuisines", []):
            d_name = sanitize_text_for_pdf(dish.get("name"))
            d_desc = sanitize_text_for_pdf(dish.get("description"))
            story.append(Paragraph(f"- <b>{d_name}:</b> {d_desc}", body_style))
            
        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>Local Beverages:</b>", body_style))
        for bev in flavors.get("beverages", []):
            b_name = sanitize_text_for_pdf(bev.get("name"))
            b_desc = sanitize_text_for_pdf(bev.get("description"))
            story.append(Paragraph(f"- <b>{b_name}:</b> {b_desc}", body_style))
            
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Culinary Hotspots:</b> {sanitize_text_for_pdf(flavors.get('hotspots'))}", body_style))
        
    story.append(Spacer(1, 15))
    story.append(Paragraph("Travel Tips", h1_style))
    tips = itinerary_data.get("travel_tips", [])
    for tip in tips:
        story.append(Paragraph(f"- {sanitize_text_for_pdf(tip)}", body_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer
