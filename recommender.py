import os
import json
import yaml
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load configuration
with open("configs/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Create run folder for reproducibility
if config.get("save_runs", True):
    run_dir = f"runs/run_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    os.makedirs(run_dir, exist_ok=True)
else:
    run_dir = "."

# Load static data
# Read package definitions
with open(config["package_definitions"], "r", encoding="utf-8") as f:
    package_definitions = f.read().strip()
# Read vendor components from txt file
with open(config["vendor_components"], "r", encoding="utf-8") as f:
    vendor_components = [line.strip() for line in f if line.strip()]
with open(config["input_profiles"], "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

# Convert to a nice bullet-list string
VENDOR_COMPONENTS_STR = "- " + "\n- ".join(vendor_components)

# Generate recommendations for one SME profile.
def get_prompt(profile):
    return f"""
    You are an experienced cybersecurity strategist working.
    Analyze the following SME profile and provide:
    1. The most suitable Green Circle managed security package, using the Green Circle security package definitions below.
    2. pick a 3–5 recommended tooling stack from typical vendors, using the vendor components list below.
    3. A 1–2 lines justification summarizing why this package and tooling stack were selected.
Return your output **only in JSON format**, including only the package, tooling_stack, and the justification.
 Do not include any text outside this JSON.  
     SME Profile:
    {json.dumps(profile, indent=2)}
    Green Circle Packages:
    {package_definitions}
    Available Vendor Components:
    {vendor_components}
    """

# ============================================================
# AGENTIC FUNCTION – query the LLM
# ============================================================
def query_model(prompt: str, max_new_tokens: int = 512) -> str:
    """Send a reasoning-style prompt to GPT-OSS 20B via Hugging Face API."""
    payload = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
       ## "model": config["model"]
        "model": config["model"]
    }
    response = requests.post(config["HF_API_URL"], headers=HEADERS, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"❌ API error {response.status_code}: {response.text}")
    data = response.json()
    if isinstance(data, list) and "generated_text" in data[0]:
        return data[0]["generated_text"].strip()
    recommendation = json.loads(data["choices"][0]["message"]['content'])
    return recommendation
# cleans and normalizes tex
def clean_text(text):
    if not text:
        return ""
    # Normalize dashes
    text = re.sub(r"[\u2010-\u2015]", "-", text)  # Replace all Unicode dash variants with "-"
    # Replace non-breaking spaces with normal spaces
    text = text.replace("\u00A0", " ").replace("\u202F", " ")
    # Remove invisible zero-width chars
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
    return text

# PDF GENERATION
def generate_sme_pdf_append(sme_results, filename):
    """
    Adds a new page for a single SME into an existing PDF.

    :param sme_result: dict with keys 'name', 'package', 'tools' (list), 'justification', 'reasoning' (optional)
    :param filename: target PDF file name
    """
    if os.path.exists(filename):
        os.remove(filename)  # Delete existing PDF to start fresh

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    story = []

    for sme in sme_results:
        # Header
        story.append(Paragraph(f"<b>SME Security Package Summary</b>", styles["Heading1"]))
        story.append(Spacer(1, 12))
        # Table
        table_data = [
            ["Field", "Value"],
            ["SME_Name", Paragraph(sme.get("SME_Name", "N/A"), normal_style)],
            ["Industry", Paragraph(sme.get("Industry", "N/A"), normal_style)],
            ["Headcount", Paragraph(str(sme.get("Headcount", "N/A")), normal_style)],
            ["Endpoints", Paragraph(str(sme.get("Endpoints", "N/A")), normal_style)],
            ["Cloud", Paragraph(sme.get("Cloud", "N/A"), normal_style)],
            ["On_Prem", Paragraph(sme.get("On_Prem", "N/A"), normal_style)],
            ["Regulatory_Drivers", Paragraph(", ".join(sme.get("Regulatory_Drivers", [])) or "N/A", normal_style)],
            ["Monthly_Budget_Band", Paragraph(sme.get("Monthly_Budget_Band", "N/A"), normal_style)],
            ["Recommended_Package", Paragraph(sme.get("Recommended_Package", "N/A"), normal_style)],
            ["Tooling_Stack", Paragraph(", ".join(sme.get("Tooling_Stack", [])) or "N/A", normal_style)],
            ["Justification", Paragraph(clean_text(sme.get("Justification", "N/A")), normal_style)],
        ]

        table = Table(table_data, colWidths=[120, 380])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("VALIGN", (0, 1), (0, -1), "MIDDLE"),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ]))

        story.append(table)
        story.append(PageBreak())  # new page per SME

    doc = SimpleDocTemplate(filename, pagesize=A4)
    doc.build(story)
    print(f"✅ PDF created: {filename}")

# --------------------------
# Start processing the SME  profiles
# --------------------------

# CONFIGURATION
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

# Run recommendations
sme_profiles = data.get("SME_Profiles", [])
summary = []

# --- Process each SME ---
for sme in sme_profiles:
    try:
        prompt = get_prompt(sme)
        response = query_model(prompt)

        # create an SME summary
        Summary_entry = {
        "SME_Name": sme["SME_Name"],
        "Industry": sme["Industry"],
        "Headcount": sme["Size"]["Headcount"],
        "Endpoints": sme["Size"]["Endpoints"],
        "Cloud": sme["Cloud_On_Prem_Mix"]["Cloud"],
        "On_Prem": sme["Cloud_On_Prem_Mix"]["On_Prem"],
        "Regulatory_Drivers":sme["Regulatory_Drivers"],
        "Monthly_Budget_Band":sme["Monthly_Budget_Band"],
        "Recommended_Package":response ["package"],
        "Tooling_Stack":response ["tooling_stack"],
        "Justification": response ["justification"]
        }
        summary.append(Summary_entry)
        print(f"✅ Finished {sme["SME_Name"]}")
    except Exception as e:
        print(f"❌ Failed to process {sme["SME_Name"]}: {e}")

    print(f"Processing {sme["SME_Name"]} …")

# --- Write summary pdf ---
pdf_path = os.path.join(run_dir, "SME_Recommendations.pdf")
generate_sme_pdf_append(summary,pdf_path)

# --- Write summary JSON ---
summary_path = os.path.join(run_dir, "SME_Summary_Table.json")
with open(summary_path, 'w', encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"\n🎯 All reports complete. Summary written to: {summary_path}")


# --- Write concise summary JSON ---
# Flatten lists into comma-separated strings
flattened_smes = []

for s in summary:
    flattened_smes.append({
        "Name": s.get("Name", "N/A"),
        "Industry": s.get("Industry", "N/A"),
        "Recommended_Package": s.get("Recommended_Package", "N/A"),
        "Tooling_Stack": ", ".join(s.get("Tooling_Stack", [])),
        "Justification": s.get("Justification", "N/A")
    })

# Write JSON
summary_path = os.path.join(run_dir, "Concise_SME_Summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(flattened_smes, f, indent=2, ensure_ascii=False)
