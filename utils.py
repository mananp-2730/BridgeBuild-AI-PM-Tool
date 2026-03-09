from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io
import re
import os
from datetime import datetime, timezone, timedelta
import json

# --- 1. TEXT & JSON HELPER FUNCTIONS ---

def convert_currency(amount, currency_type):
    try:
        clean_str = ''.join(c for c in str(amount).split('-')[0] if c.isdigit())
        clean_amount = int(clean_str) if clean_str else 0
        if "USD" in currency_type:
            return f"USD {clean_amount:,}"
        else:
            inr_amount = clean_amount * 85
            return f"INR {inr_amount:,}"
    except:
        return str(amount).replace("₹", "INR ")

def parse_cost_avg(cost_string):
    try:
        clean = str(cost_string).replace("$", "").replace(",", "").replace("USD", "").replace("₹", "").replace("INR", "").strip()
        if "-" in clean:
            parts = clean.split("-")
            low = int(parts[0].strip())
            high = int(parts[1].strip())
            return (low + high) // 2
        else:
            return int(clean)
    except:
        return 0

def clean_json_output(raw_text):
    text = re.sub(r"^```json\s*", "", raw_text, flags=re.MULTILINE)
    text = re.sub(r"^```\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    return text.strip()

def safe_parse_json(raw_text):
    """Catches AI hallucinations or broken formatting gracefully."""
    try:
        cleaned = clean_json_output(raw_text)
        return json.loads(cleaned), None
    except json.JSONDecodeError:
        return None, "⚠️ The AI Engine returned a malformed response. Please click 'Generate' again to retry."
    except Exception as e:
        return None, f"⚠️ An unexpected error occurred: {str(e)}"

def format_cost_range(raw_cost, currency):
    raw_cost = str(raw_cost)
    if "-" in raw_cost:
        parts = raw_cost.split("-")
        low = convert_currency(parts[0].strip(), currency)
        high = convert_currency(parts[1].strip(), currency)
        return f"{low} - {high}"
    return convert_currency(raw_cost, currency)

def generate_jira_format(data, currency="USD ($)"):
    p1_cost = format_cost_range(data.get('budget_estimate_usd', '0'), currency)
    p2_cost = format_cost_range(data.get('phase_2_budget_usd', '0'), currency)
    
    jira_text = f"h1. {data.get('ticket_name', 'Untitled Ticket')}\n"
    jira_text += f"h2. Overview\n* **Complexity:** {data.get('complexity_score', 'N/A')}\n\n"
    jira_text += f"h2. Phase 1: Core MVP\n* **Est. Time:** {data.get('development_time', 'N/A')}\n* **Est. Budget:** {p1_cost}\n"
    
    if "mvp_user_stories" in data:
        for item in data.get('mvp_user_stories', []):
            jira_text += f"\n*Story:* {item.get('story')}\n"
            for ac in item.get('acceptance_criteria', []):
                jira_text += f"** {ac}\n"
    else:
        jira_text += chr(10).join([f'* {feat}' for feat in data.get('mvp_features', [])]) + "\n"

    jira_text += f"\nh2. Technical Risks\n{{panel:title=Risks|borderStyle=dashed|borderColor=#ff0000}}\n"
    jira_text += chr(10).join([f'- {risk}' for risk in data.get('technical_risks', [])]) + "\n{panel}\n"
    
    return jira_text


# --- 2. REPORTLAB PDF DRAWING HELPERS ---

def safe_text(text):
    """Sanitizes text to prevent reportlab black square rendering errors."""
    return str(text).replace("₹", "INR ").encode('ascii', 'ignore').decode('ascii')

def draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=11, line_height=14):
    c.setFont(font_name, font_size)
    words = safe_text(text).split(' ')
    line = ""
    for word in words:
        if c.stringWidth(line + word + " ", font_name, font_size) < max_width:
            line += word + " "
        else:
            c.drawString(x, y, line.strip())
            y -= line_height
            line = word + " "
    if line:
        c.drawString(x, y, line.strip())
        y -= line_height
    return y

def check_page_break(c, current_y, height, threshold=100):
    if current_y < threshold:
        c.showPage()
        return height - 50
    return current_y

def draw_pdf_header(c, width, height, report_title):
    c.setFillColorRGB(0.004, 0.129, 0.412) 
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, height - 60, report_title)
    
    ist = timezone(timedelta(hours=5, minutes=30))
    date_str = datetime.now(ist).strftime("%Y-%m-%d %H:%M IST")
    
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 80, safe_text(f"Generated on: {date_str} | BridgeBuild AI"))
    
    if os.path.exists("Logo_bg_removed.png"):
        c.drawImage("Logo_bg_removed.png", width - 100, height - 90, width=80, height=80, mask='auto')


# --- 3. DEDICATED PDF ENGINES ---

def create_pm_pdf(ticket_data, currency="USD ($)"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    draw_pdf_header(c, width, height, "Engineering Ticket Report")
    
    y = height - 140
    c.setFillColor(colors.black)

    # Summary
    name = ticket_data.get("ticket_name", ticket_data.get("summary", "Untitled"))
    y = draw_wrapped_text(c, f"Project: {name}", 40, y, 500, "Helvetica-Bold", 16)
    y -= 15
    y = draw_wrapped_text(c, ticket_data.get("summary", "No summary provided."), 40, y, 520, "Helvetica", 11)
    y -= 20

    # Phase 1
    p1_budget = format_cost_range(ticket_data.get('budget_estimate_usd', '0'), currency)
    y = check_page_break(c, y, height)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Phase 1: Core MVP"))
    y -= 20
    c.setFillColor(colors.black)
    c.drawString(40, y, safe_text(f"Est. Time: {ticket_data.get('development_time', 'N/A')} | Est. Budget: {p1_budget}"))
    y -= 20
    
    # MVP Stories & ACs
    if "mvp_user_stories" in ticket_data:
        for item in ticket_data.get("mvp_user_stories", []):
            y = check_page_break(c, y, height)
            y = draw_wrapped_text(c, f"Story: {item.get('story', '')}", 40, y, 500, "Helvetica-Bold", 10)
            for ac in item.get("acceptance_criteria", []):
                y = check_page_break(c, y, height)
                c.drawString(50, y, "-")
                y = draw_wrapped_text(c, f"AC: {ac}", 60, y, 480, "Helvetica", 10)
            y -= 10
    else:
        for feat in ticket_data.get("mvp_features", []):
            y = check_page_break(c, y, height)
            c.drawString(45, y, "-")
            y = draw_wrapped_text(c, feat, 60, y, 480, "Helvetica", 11)
    
    # Phase 2
    y -= 10
    y = check_page_break(c, y, height)
    p2_budget = format_cost_range(ticket_data.get('phase_2_budget_usd', '0'), currency)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Phase 2: Future Enhancements"))
    y -= 20
    c.setFillColor(colors.black)
    c.drawString(40, y, safe_text(f"Est. Extra Time: {ticket_data.get('phase_2_time', 'N/A')} | Est. Extra Budget: {p2_budget}"))
    y -= 20
    
    for feat in ticket_data.get("phase_2_features", []):
        y = check_page_break(c, y, height)
        c.drawString(45, y, "-")
        y = draw_wrapped_text(c, feat, 60, y, 480, "Helvetica", 11)
        y -= 5

    # Risks
    y -= 10
    y = check_page_break(c, y, height)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Technical Risks"))
    y -= 20
    c.setFillColor(colors.black)
    for risk in ticket_data.get("technical_risks", []):
        y = check_page_break(c, y, height)
        c.drawString(45, y, "-")
        y = draw_wrapped_text(c, risk, 60, y, 490, "Helvetica", 11)
        y -= 5

    # Tech Stack
    y -= 10
    y = check_page_break(c, y, height)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Suggested Tech Stack"))
    y -= 20
    c.setFillColor(colors.black)
    for item in ticket_data.get("suggested_stack", []):
        y = check_page_break(c, y, height)
        c.drawString(45, y, "-")
        y = draw_wrapped_text(c, item, 60, y, 490, "Helvetica", 11)
        y -= 5

    c.save()
    buffer.seek(0)
    return buffer
    
def create_sales_pdf(ticket_data, currency="USD ($)"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    draw_pdf_header(c, width, height, "Sales & Feasibility Report")
    
    y = height - 140
    c.setFillColor(colors.black)
    y = draw_wrapped_text(c, f"Project: {ticket_data.get('summary', 'Untitled')[:60]}...", 40, y, 500, "Helvetica-Bold", 16)
    y -= 20

    y = draw_wrapped_text(c, f"Feasibility Score: {ticket_data.get('feasibility_score', 'N/A')}", 40, y, 500, "Helvetica-Bold", 12)
    budget = format_cost_range(ticket_data.get('mvp_budget_usd', '0'), currency)
    y = draw_wrapped_text(c, f"Estimated Budget: {budget}", 40, y, 500, "Helvetica", 12)
    y -= 20

    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Critical 'Ask' List for Client:"))
    y -= 20
    c.setFillColor(colors.black)
    for q in ticket_data.get("ask_list", []):
        y = check_page_break(c, y, height)
        c.drawString(45, y, "*")
        y = draw_wrapped_text(c, q, 60, y, 480, "Helvetica", 11)
        y -= 10

    c.save()
    buffer.seek(0)
    return buffer

def create_engineering_pdf(ticket_data, currency="USD ($)"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    draw_pdf_header(c, width, height, "Engineering Architecture Report")
    
    y = height - 140
    c.setFillColor(colors.black)
    y = draw_wrapped_text(c, "System Architecture", 40, y, 500, "Helvetica-Bold", 16)
    y -= 10
    y = draw_wrapped_text(c, ticket_data.get("system_architecture", "N/A"), 40, y, 500, "Helvetica", 11)
    y -= 20

    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Database Schema"))
    y -= 20
    c.setFillColor(colors.black)
    for table in ticket_data.get("database_schema", []):
        y = check_page_break(c, y, height)
        y = draw_wrapped_text(c, f"Table: {table.get('table_name', 'Unknown')}", 40, y, 500, "Helvetica-Bold", 12)
        for col in table.get("columns", []):
            y = check_page_break(c, y, height)
            y = draw_wrapped_text(c, f"- {col}", 60, y, 480, "Helvetica", 11)
        y -= 10

    c.save()
    buffer.seek(0)
    return buffer

def create_design_pdf(ticket_data, currency="USD ($)"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    draw_pdf_header(c, width, height, "UX/UI Design Specification")
    
    y = height - 140
    c.setFillColor(colors.black)
    y = draw_wrapped_text(c, "Core Vibe & Direction", 40, y, 500, "Helvetica-Bold", 16)
    y -= 10
    y = draw_wrapped_text(c, ticket_data.get("core_vibe", "N/A"), 40, y, 500, "Helvetica", 11)
    y -= 20

    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Color Palette (Hex Codes)"))
    y -= 20
    c.setFillColor(colors.black)
    for color in ticket_data.get("color_palette_hex", []):
        y = check_page_break(c, y, height)
        y = draw_wrapped_text(c, f"- {color}", 60, y, 480, "Helvetica", 11)
    
    c.save()
    buffer.seek(0)
    return buffer
