from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
import json
import base64
from fpdf import FPDF

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = "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"

# ── Models ────────────────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    plan_name: str
    calorie_target: int
    protein_pct: int
    carbs_pct: int
    fat_pct: int

class RepasItem(BaseModel):
    type: str
    nom: str
    description: str
    calories: int
    proteines: int
    glucides: int
    lipides: int
    ingredients: List[str]

class PDFRequest(BaseModel):
    plan_name: str
    calorie_target: int
    protein_pct: int
    carbs_pct: int
    fat_pct: int
    repas: List[RepasItem]

# ── Generate Meals ─────────────────────────────────────────────────────────────

@app.post("/generate-meals")
async def generate_meals(plan: PlanRequest):
    protein_g = round((plan.calorie_target * plan.protein_pct / 100) / 4)
    carbs_g   = round((plan.calorie_target * plan.carbs_pct   / 100) / 4)
    fat_g     = round((plan.calorie_target * plan.fat_pct     / 100) / 9)

    prompt = f"""Tu es nutritionniste expert. Génère un plan repas complet pour une journée.
Plan: {plan.plan_name}, {plan.calorie_target} kcal, proteines {plan.protein_pct}% ({protein_g}g), glucides {plan.carbs_pct}% ({carbs_g}g), lipides {plan.fat_pct}% ({fat_g}g).
Reponds UNIQUEMENT en JSON valide, rien d'autre, pas de texte avant ou apres:
{{"repas":[{{"type":"Petit dejeuner","nom":"nom","description":"description","calories":400,"proteines":20,"glucides":45,"lipides":12,"ingredients":["i1","i2","i3"]}},{{"type":"Dejeuner","nom":"nom","description":"description","calories":600,"proteines":35,"glucides":65,"lipides":18,"ingredients":["i1","i2","i3"]}},{{"type":"Snack","nom":"nom","description":"description","calories":200,"proteines":10,"glucides":25,"lipides":6,"ingredients":["i1","i2"]}},{{"type":"Diner","nom":"nom","description":"description","calories":500,"proteines":30,"glucides":50,"lipides":15,"ingredients":["i1","i2","i3"]}}]}}"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Tu es un nutritionniste expert. Reponds UNIQUEMENT en JSON valide sans aucun texte avant ou apres."},
                    {"role": "user",   "content": prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=60.0
        )
        data = response.json()
        if "choices" not in data:
            return {"error": str(data)}
        text   = data["choices"][0]["message"]["content"]
        result = json.loads(text)
        return result

# ── Generate PDF ───────────────────────────────────────────────────────────────

@app.post("/generate-pdf")
async def generate_pdf(req: PDFRequest):
    protein_g = round((req.calorie_target * req.protein_pct / 100) / 4)
    carbs_g   = round((req.calorie_target * req.carbs_pct   / 100) / 4)
    fat_g     = round((req.calorie_target * req.fat_pct     / 100) / 9)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_fill_color(108, 99, 255)
    pdf.rect(0, 0, 210, 42, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "Plan Nutritionnel", ln=True, align="C")
    pdf.set_font("Helvetica", "", 13)
    pdf.set_xy(10, 22)
    pdf.cell(0, 10, req.plan_name, ln=True, align="C")

    # Macros summary
    pdf.set_xy(10, 50)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Objectifs nutritionnels", ln=True)
    pdf.set_draw_color(108, 99, 255)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    col_w   = 45
    x_start = 10
    headers = ["Calories", "Proteines", "Glucides", "Lipides"]
    values  = [
        f"{req.calorie_target} kcal",
        f"{protein_g}g ({req.protein_pct}%)",
        f"{carbs_g}g ({req.carbs_pct}%)",
        f"{fat_g}g ({req.fat_pct}%)"
    ]

    y_row = pdf.get_y()
    for i, h in enumerate(headers):
        pdf.set_xy(x_start + i * col_w, y_row)
        pdf.set_fill_color(237, 233, 255)
        pdf.set_text_color(108, 99, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(col_w - 2, 8, h, align="C", fill=True)
    pdf.ln(8)
    y_row = pdf.get_y()
    for i, v in enumerate(values):
        pdf.set_xy(x_start + i * col_w, y_row)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(col_w - 2, 7, v, align="C")
    pdf.ln(14)

    # Repas
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 8, "Detail des repas", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    badge_colors = {
        "Petit dejeuner": (255, 180, 80),
        "Dejeuner":       (80,  190, 140),
        "Snack":          (180, 130, 255),
        "Diner":          (80,  150, 255),
    }

    for repas in req.repas:
        r, g, b = badge_colors.get(repas.type, (200, 200, 200))

        # Badge type
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(38, 7, repas.type, align="C", fill=True, ln=True)
        pdf.ln(1)

        # Nom
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 7, repas.nom, ln=True)

        # Description
        pdf.set_text_color(120, 120, 120)
        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(0, 5, repas.description)
        pdf.ln(2)

        # Macros
        macros = [
            ("Calories",  f"{repas.calories} kcal"),
            ("Proteines", f"{repas.proteines}g"),
            ("Glucides",  f"{repas.glucides}g"),
            ("Lipides",   f"{repas.lipides}g"),
        ]
        y_m = pdf.get_y()
        for i, (label, val) in enumerate(macros):
            pdf.set_xy(x_start + i * col_w, y_m)
            pdf.set_fill_color(240, 238, 255)
            pdf.set_text_color(108, 99, 255)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(col_w - 2, 7, val, align="C", fill=True)
        pdf.ln(7)
        y_m = pdf.get_y()
        for i, (label, val) in enumerate(macros):
            pdf.set_xy(x_start + i * col_w, y_m)
            pdf.set_text_color(150, 150, 150)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(col_w - 2, 5, label, align="C")
        pdf.ln(8)

        # Ingredients
        pdf.set_text_color(80, 80, 80)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, "Ingredients:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 5, "  -  ".join(repas.ingredients))
        pdf.ln(4)

        # Separator
        pdf.set_draw_color(220, 220, 220)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    # Footer
    pdf.set_y(-18)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(0, 10, "Genere par GymFit AI  |  Plan personnalise", align="C")

    # Return as base64
    pdf_bytes  = bytes(pdf.output())
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    return {"pdf_base64": pdf_base64, "filename": f"plan_{req.plan_name}.pdf"}

# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "API is running"}
