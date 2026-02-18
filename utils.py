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
        # If amount is a string like "$5,000", clean it first
        if isinstance(amount, str):
            clean_amount = int(amount.replace("$", "").replace(",", "").split("-")[0].strip())
        else:
            clean_amount = int(amount)

        if currency_type == "USD ($)":
            return f"${clean_amount:,}"
        else:
            # Approx rate: 1 USD = 85 INR
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
* **Est. Time:** {data.get('development_time', 'N/A')}
* **Est. Budget:** {data.get('budget_estimate_usd', '0')}
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
    Generates a professional PDF with Duke Blue branding and logos.
    Returns a BytesIO buffer.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # --- HEADER SECTION ---
    # Draw Duke Blue Header Bar
    c.setFillColorRGB(0.004, 0.129, 0.412) # #012169 (Duke Blue)
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    # Add White Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, height - 60, "Engineering Ticket Report")
    
    # Add Date/Subtitle
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 80, f"Generated on: {date_str} | BridgeBuild AI")
    
    # Add Logo (Right aligned)
    # Check if logo exists to avoid crash
    logo_path = "Logo_bg_removed.png"
    if os.path.exists(logo_path):
        # x, y, width, height (Adjusted to sit nicely in the blue bar)
        c.drawImage(logo_path, width - 100, height - 90, width=80, height=80, mask='auto')

    # --- CONTENT SECTION ---
    y = height - 140
    c.setFillColor(colors.black)
    
    # Helper to print label: value pairs
    def print_field(label, value, y_pos):
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0.004, 0.129, 0.412) # Blue Label
        c.drawString(40, y_pos, f"{label}:")
        
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black) # Black Value
        
        # Handle lists (e.g., Tech Stack)
        if isinstance(value, list):
            text_val = ", ".join(value)
        else:
            text_val = str(value)
            
        # Basic text truncation to avoid overwrite
        if len(text_val) > 70:
            text_val = text_val[:70] + "..."
            
        c.drawString(160, y_pos, text_val)
        return y_pos - 25

    # 1. Key Metrics
    y = print_field("Ticket Name", ticket_data.get("ticket_name", "Untitled"), y)
    y = print_field("Complexity", ticket_data.get("complexity_score", "N/A"), y)
    y = print_field("Est. Time", ticket_data.get("development_time", "N/A"), y)
    y = print_field("Est. Cost", f"${ticket_data.get('budget_estimate_usd', '0')}", y)
    
    y -= 10
    c.setStrokeColor(colors.lightgrey)
    c.line(40, y, width-40, y) # Divider Line
    y -= 30

    # 2. Description (Text Wrapping)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "Description & Requirements")
    y -= 20
    
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    description = ticket_data.get("description", "No description provided.")
    
    # Simple text wrap logic
    words = description.split(' ')
    line = ""
    for word in words:
        if len(line + word) < 90:
            line += word + " "
        else:
            c.drawString(40, y, line)
            y -= 15
            line = word + " "
    c.drawString(40, y, line) # Last line
    y -= 30

    # 3. Acceptance Criteria
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "Acceptance Criteria")
    y -= 20
    
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    criteria = ticket_data.get("acceptance_criteria", [])
    
    for item in criteria:
        c.drawString(50, y, f"• {item}")
        y -= 15
        if y < 50: # New page check (basic)
            c.showPage()
            y = height - 50

    # --- FOOTER ---
    c.save()
    buffer.seek(0)
    return buffer
