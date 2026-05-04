import re
import json

# ==========================================
# TEXT, CURRENCY & JSON HELPER FUNCTIONS
# ==========================================

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
