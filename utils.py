from fpdf import FPDF

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

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

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
    """
    Parses a string like '5000-8000' or '5000' into an integer average.
    Returns 0 if parsing fails.
    """
    try:
        # Remove currency symbols and commas
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
