from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import re

def convert_currency(usd_amount_str, target_currency):
    try:
        clean_amount = int(usd_amount_str.replace("$", "").replace(",", "").replace("-", "0").split(" ")[0])
        if target_currency == "USD ($)":
            return f"${clean_amount:,}"
        else:
            inr_amount = clean_amount * 85
            return f"₹{inr_amount:,}"
    except:
        return usd_amount_str

# --- NEW PDF FUNCTION ---
def create_pdf(ticket_data):
    """
    Generates a structured PDF file from the ticket JSON data.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # 1. Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "BridgeBuild AI - Engineering Ticket")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, "Generated Technical Requirements & Cost Estimate")
    c.line(50, height - 80, width - 50, height - 80)
    
    # 2. Key Data Table
    y = height - 120
    
    def print_row(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"{label}:")
        c.setFont("Helvetica", 12)
        # Handle list or string
        if isinstance(value, list):
            text_val = ", ".join(value)
        else:
            text_val = str(value)
        c.drawString(180, y, text_val[:60]) # Truncate to fit page
        y -= 25

    print_row("Complexity", ticket_data.get("complexity_score", "N/A"))
    print_row("Dev Time", ticket_data.get("development_time", "N/A"))
    print_row("Budget (Est)", f"${ticket_data.get('budget_estimate_usd', '0')}")
    print_row("Tech Stack", ticket_data.get("suggested_stack", []))
    
    y -= 10
    c.line(50, y, width - 50, y)
    y -= 30
    
    # 3. Summary & Risks
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Technical Summary:")
    y -= 20
    c.setFont("Helvetica", 11)
    
    # Simple text wrapping for summary
    summary = ticket_data.get("summary", "No summary provided.")
    # Split into chunks of 90 chars roughly
    start = 0
    for i in range(3): # Print max 3 lines of summary
        if start < len(summary):
            end = start + 90
            c.drawString(50, y, summary[start:end])
            y -= 15
            start = end
            
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Key Risks:")
    y -= 20
    c.setFont("Helvetica", 11)
    
    risks = ticket_data.get("technical_risks", [])
    for risk in risks[:5]: # List max 5 risks
        c.drawString(60, y, f"• {risk}")
        y -= 15

    # 4. Save
    c.save()
    buffer.seek(0)
    return buffer

# --- EXISTING FUNCTIONS KEPT AS IS ---
def generate_jira_format(data):
    jira_text = f"""
h1. {data.get('summary')}
h2. Overview
* **Complexity:** {data.get('complexity_score')}
* **Est. Time:** {data.get('development_time')}
* **Est. Budget:** {data.get('budget_estimate_usd')}
h2. Technical Risks
{{panel:title=Risks|borderStyle=dashed|borderColor=#ff0000}}
{chr(10).join([f'- {risk}' for risk in data.get('technical_risks', [])])}
{{panel}}
h2. Tech Stack
{{code:bash}}
{chr(10).join(data.get('suggested_stack', []))}
{{code}}
h2. Data Schema
||Entity Name||
{chr(10).join([f'|{entity}|' for entity in data.get('primary_entities', [])])}
    """
    return jira_text

def parse_cost_avg(cost_string):
    try:
        clean = cost_string.replace("$", "").replace(",", "").replace("USD", "").replace("₹", "").strip()
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
