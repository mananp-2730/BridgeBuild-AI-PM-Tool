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

# --- 2. THE PRO PDF GENERATOR (SMART WRAP VERSION) ---
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
        """
        Draws text that automatically wraps to the next line if it gets too long.
        Returns the new Y position after writing.
        """
        c.setFont(font_name, font_size)
        words = text.split(' ')
        line = ""
        
        for word in words:
            # Check if adding the next word exceeds the max width
            if c.stringWidth(line + word + " ", font_name, font_size) < max_width:
                line += word + " "
            else:
                # Draw current line and move down
                c.drawString(x, y, line.strip())
                y -= line_height
                line = word + " "
        
        # Draw the last remaining line
        if line:
            c.drawString(x, y, line.strip())
            y -= line_height
            
        return y

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
    
    # 1. Key Metrics Table
    def print_field(label, value, y_pos):
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0.004, 0.129, 0.412) 
        c.drawString(40, y_pos, f"{label}:")
        
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black) 
        # Use simple string for metrics, truncated if absolutely massive
        text_val = str(value)
        if len(text_val) > 60: text_val = text_val[:60] + "..."
        c.drawString(160, y_pos, text_val)
        return y_pos - 25

    # Ticket Name (Handle long names by wrapping)
    name = ticket_data.get("ticket_name", ticket_data.get("summary", "Untitled"))
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "Ticket Name:")
    c.setFillColor(colors.black)
    # Wrap the name if it's super long
    y = draw_wrapped_text(c, name, 160, y, 400, "Helvetica", 12) 
    y -= 10 # Extra spacer after name

    y = print_field("Complexity", ticket_data.get("complexity_score", "N/A"), y)
    y = print_field("Est. Time", ticket_data.get("development_time", "N/A"), y)
    
    # Cost Formatting
    raw_cost = ticket_data.get('budget_estimate_usd', '0')
    formatted_cost = convert_currency(raw_cost, "USD ($)")
    y = print_field("Est. Cost", formatted_cost, y)
    
    y -= 10
    c.setStrokeColor(colors.lightgrey)
    c.line(40, y, width-40, y)
    y -= 30

    # 2. Description
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "Technical Summary")
    y -= 25
    
    c.setFillColor(colors.black)
    description = ticket_data.get("summary", "No summary provided.")
    # Wrap text within 500px width
    y = draw_wrapped_text(c, description, 40, y, 520, "Helvetica", 11)
    y -= 20

    # 3. Technical Risks
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "⚠️ Technical Risks")
    y -= 25
    
    c.setFillColor(colors.black)
    risks = ticket_data.get("technical_risks", [])
    if not risks:
        c.drawString(50, y, "• No significant risks detected.")
        y -= 15
    else:
        for risk in risks:
            # Bullet Point Logic
            c.drawString(45, y, "•") # Draw bullet
            # Draw text slightly indented (x=60), wrapping at 500px width
            y = draw_wrapped_text(c, risk, 60, y, 490, "Helvetica", 11)
            y -= 5 # Extra breathing room between items

    y -= 15

    # 4. Tech Stack
    # Check if we are running out of space
    if y < 150: 
        c.showPage() # Start new page if low on space
        y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, "🏗 Suggested Tech Stack")
    y -= 25
    
    c.setFillColor(colors.black)
    stack = ticket_data.get("suggested_stack", [])
    if not stack:
         c.drawString(50, y, "• No specific stack suggested.")
    else:
        for item in stack:
            c.drawString(45, y, "•")
            y = draw_wrapped_text(c, item, 60, y, 490, "Helvetica", 11)
            y -= 5

    c.save()
    buffer.seek(0)
    return buffer
