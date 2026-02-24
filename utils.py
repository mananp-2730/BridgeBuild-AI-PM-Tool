from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io
import re
import os
from datetime import datetime, timezone, timedelta

# --- 1. HELPER FUNCTIONS ---
def convert_currency(amount, currency_type):
    try:
        # Extract only the digits from the first part of the range
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
    
    jira_text = f"""
h1. {data.get('ticket_name', 'Untitled Ticket')}
h2. Overview
* **Complexity:** {data.get('complexity_score', 'N/A')}

h2. Phase 1: Core MVP
* **Est. Time:** {data.get('development_time', 'N/A')}
* **Est. Budget:** {p1_cost}
"""
    if "mvp_user_stories" in data:
        for item in data.get('mvp_user_stories', []):
            jira_text += f"\n*Story:* {item.get('story')}\n"
            for ac in item.get('acceptance_criteria', []):
                jira_text += f"** {ac}\n"
    else:
        jira_text += chr(10).join([f'* {feat}' for feat in data.get('mvp_features', [])]) + "\n"

    jira_text += f"""
h2. Phase 2: Future Enhancements
* **Est. Extra Time:** {data.get('phase_2_time', 'N/A')}
* **Est. Extra Budget:** {p2_cost}
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
# ADDED 'ticket_type' parameter!
def create_pdf(ticket_data, currency="USD ($)", ticket_type="detailed"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # THE ULTIMATE SANITIZER: Stops black squares permanently
    def safe_text(text):
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

    def check_page_break(c, current_y, threshold=100):
        if current_y < threshold:
            c.showPage()
            return height - 50
        return current_y

    # HEADER SECTION
    c.setFillColorRGB(0.004, 0.129, 0.412) 
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    
    # Change title based on Brief vs Detailed
    report_title = "Executive Scoping Report" if ticket_type == "brief" else "Engineering Ticket Report"
    c.drawString(40, height - 60, report_title)
    
    ist = timezone(timedelta(hours=5, minutes=30))
    date_str = datetime.now(ist).strftime("%Y-%m-%d %H:%M IST")
    
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 80, safe_text(f"Generated on: {date_str} | BridgeBuild AI"))
    
    if os.path.exists("Logo_bg_removed.png"):
        c.drawImage("Logo_bg_removed.png", width - 100, height - 90, width=80, height=80, mask='auto')

    # CONTENT SECTION
    y = height - 140
    c.setFillColor(colors.black)

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

    p1_budget = format_cost_range(ticket_data.get('budget_estimate_usd', '0'), currency)
    p2_budget = format_cost_range(ticket_data.get('phase_2_budget_usd', '0'), currency)

    # 1. Phase 1: MVP
    y = check_page_break(c, y)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Phase 1: Core MVP"))
    y -= 20
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, safe_text(f"Est. Time: {ticket_data.get('development_time', 'N/A')} | Est. Budget: {p1_budget}"))
    y -= 20
    
    # SMART LOGIC: Show ACs only if Detailed!
    if "mvp_user_stories" in ticket_data:
        for item in ticket_data.get("mvp_user_stories", []):
            y = check_page_break(c, y)
            
            if ticket_type == "detailed":
                c.setFont("Helvetica-Bold", 10)
                y = draw_wrapped_text(c, f"Story: {item.get('story', '')}", 40, y, 500, "Helvetica-Bold", 10)
                c.setFont("Helvetica", 10)
                for ac in item.get("acceptance_criteria", []):
                    y = check_page_break(c, y)
                    c.drawString(50, y, "-")
                    y = draw_wrapped_text(c, f"AC: {ac}", 60, y, 480, "Helvetica", 10)
                y -= 10
            else:
                # Brief Version: Just print the story as a bullet point
                c.setFont("Helvetica", 11)
                c.drawString(45, y, "-")
                y = draw_wrapped_text(c, item.get('story', ''), 60, y, 490, "Helvetica", 11)
                y -= 5
    else:
        c.setFont("Helvetica", 11)
        for feat in ticket_data.get("mvp_features", []):
            y = check_page_break(c, y)
            c.drawString(45, y, "-")
            y = draw_wrapped_text(c, feat, 60, y, 490, "Helvetica", 11)
            y -= 5
    y -= 15

    # 2. Phase 2: Enhancements
    y = check_page_break(c, y)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Phase 2: Future Enhancements"))
    y -= 20
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, safe_text(f"Est. Extra Time: {ticket_data.get('phase_2_time', 'N/A')} | Est. Extra Budget: {p2_budget}"))
    y -= 20
    
    c.setFont("Helvetica", 11)
    for feat in ticket_data.get("phase_2_features", []):
        y = check_page_break(c, y)
        c.drawString(45, y, "-")
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
    c.drawString(40, y, safe_text("Technical Risks"))
    y -= 20
    
    c.setFillColor(colors.black)
    for risk in ticket_data.get("technical_risks", []):
        y = check_page_break(c, y)
        c.drawString(45, y, "-")
        y = draw_wrapped_text(c, risk, 60, y, 490, "Helvetica", 11)
        y -= 5
    y -= 15

    # 4. Tech Stack
    y = check_page_break(c, y)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, safe_text("Suggested Tech Stack"))
    y -= 20
    
    c.setFillColor(colors.black)
    for item in ticket_data.get("suggested_stack", []):
        y = check_page_break(c, y)
        c.drawString(45, y, "-")
        y = draw_wrapped_text(c, item, 60, y, 490, "Helvetica", 11)
        y -= 5

    c.save()
    buffer.seek(0)
    return buffer
