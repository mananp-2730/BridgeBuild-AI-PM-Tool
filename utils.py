from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io
import re
import os
from datetime import datetime

# --- 1. HELPER FUNCTIONS ---
def convert_currency(amount, currency_type):
    """
    Converts a raw number (e.g., 5000) into formatted string ($5,000 or ₹4,25,000).
    """
    try:
        if isinstance(amount, str):
            clean_amount = int(amount.replace("$", "").replace(",", "").split("-")[0].strip())
        else:
            clean_amount = int(amount)

        if currency_type == "USD ($)":
            return f"${clean_amount:,}"
        else:
            inr_amount = clean_amount * 85
            return f"₹{inr_amount:,}"
    except:
        return str(amount)

def parse_cost_avg(cost_string):
    """
    Parses a cost range string (e.g., "$5,000 - $8,000") and returns average integer.
    """
    try:
        clean = str(cost_string).replace("$", "").replace(",", "").replace("USD", "").replace("₹", "").strip()
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
    """
    Removes markdown code blocks from AI response to get pure JSON.
    """
    text = re.sub(r"^```json\s*", "", raw_text, flags=re.MULTILINE)
    text = re.sub(r"^```\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    return text.strip()

def generate_jira_format(data):
    """
    Converts JSON data into JIRA/Confluence markup format.
    """
    jira_text = f"""
h1. {data.get('ticket_name', 'Untitled Ticket')}

h2. Overview
* **Complexity:** {data.get('complexity_score', 'N/A')}

h2. Phase 1: Core MVP
* **Est. Time:** {data.get('development_time', 'N/A')}
* **Est. Budget:** {data.get('budget_estimate_usd', '0')}
{chr(10).join([f'* {feat}' for feat in data.get('mvp_features', [])])}

h2. Phase 2: Future Enhancements
* **Est. Extra Time:** {data.get('phase_2_time', 'N/A')}
* **Est. Extra Budget:** {data.get('phase_2_budget_usd', '0')}
{chr(10).join([f'* {feat}' for feat in data.get('phase_2_features', [])])}

h2. Technical Risks
{{panel:title=Risks|borderStyle=dashed|borderColor=#ff0000}}
{chr(10).join([f'- {risk}' for risk in data.get('technical_risks', [])])}
{{panel}}

h2. Tech Stack
{{code:bash}}
{chr(10).join(data.get('suggested_stack', []))}
{{code}}
    """
    return jira_text

# --- 2. THE PRO PDF GENERATOR ---
def create_pdf(ticket_data):
    """
    Generates a professional PDF with Duke Blue branding.
    Includes SMART TEXT WRAPPING to prevent cut-off text.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # --- HELPER: Smart Text Wrapper ---
    def draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=11, line_height=14):
        c.setFont(font_name, font_size)
        words = text.split(' ')
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

    # --- HELPER: Page Break Check ---
    def check_page_break(c, current_y, threshold=100):
        if current_y < threshold:
            c.showPage()
            return height - 50
        return current_y

    # --- HEADER SECTION ---
    c.setFillColorRGB(0.004, 0.129, 0.412) # Duke Blue
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, height - 60, "Engineering Ticket Report")
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 80, f"Generated on: {date_str} | BridgeBuild AI")
    
    if os.path.exists("Logo_bg_removed.png"):
        c.drawImage("Logo_bg_removed.png", width - 100, height - 90, width=80, height=80, mask='auto')

    # --- CONTENT SECTION ---
    y = height - 140
    c.setFillColor(colors.black)

    # Title & Summary
    name = ticket_data.get("ticket_name", ticket_data.get("summary", "Untitled"))
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    y = draw_wrapped_text(c, f"Project: {name}", 40, y, 500, "Helvetica-Bold", 16)
    y -= 15
    
    c.setFillColor(colors.black)
    description = ticket_data.get("summary", "No summary provided.")
    y = draw_wrapped_text(c, description, 40, y, 520, "Helvetica", 11)
    y -= 20

    c.setStrokeColor(colors.lightgrey)
    c.line(40, y, width-40, y)
    y -= 25

    # 1. Phase 1: MVP
    y = check_page_break(c, y)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "Phase 1: Core MVP")
    y -= 20
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, f"Est. Time: {ticket_data.get('development_time', 'N/A')} | Est. Budget: ${ticket_data.get('budget_estimate_usd', '0')}")
    y -= 20
    
    c.setFont("Helvetica", 11)
    for feat in ticket_data.get("mvp_features", []):
        y = check_page_break(c, y)
        c.drawString(45, y, "•")
        y = draw_wrapped_text(c, feat, 60, y, 490, "Helvetica", 11)
        y -= 5
    y -= 15

    # 2. Phase 2: Enhancements
    y = check_page_break(c, y)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "Phase 2: Future Enhancements")
    y -= 20
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, f"Est. Extra Time: {ticket_data.get('phase_2_time', 'N/A')} | Est. Extra Budget: ${ticket_data.get('phase_2_budget_usd', '0')}")
    y -= 20
    
    c.setFont("Helvetica", 11)
    for feat in ticket_data.get("phase_2_features", []):
        y = check_page_break(c, y)
        c.drawString(45, y, "•")
        y = draw_wrapped_text(c, feat, 60, y, 490, "Helvetica", 11)
        y -= 5
    y -= 20

    c.setStrokeColor(colors.lightgrey)
    c.line(40, y, width-40, y)
    y -= 25

    # 3. Technical Risks
    y = check_page_break(c, y)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "Technical Risks")
    y -= 20
    
    c.setFillColor(colors.black)
    for risk in ticket_data.get("technical_risks", []):
        y = check_page_break(c, y)
        c.drawString(45, y, "•")
        y = draw_wrapped_text(c, risk, 60, y, 490, "Helvetica", 11)
        y -= 5
    y -= 15

    # 4. Tech Stack
    y = check_page_break(c, y)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "Suggested Tech Stack")
    y -= 20
    
    c.setFillColor(colors.black)
    for item in ticket_data.get("suggested_stack", []):
        y = check_page_break(c, y)
        c.drawString(45, y, "•")
        y = draw_wrapped_text(c, item, 60, y, 490, "Helvetica", 11)
        y -= 5

    c.save()
    buffer.seek(0)
    return buffer
