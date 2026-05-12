from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = "AIzaSyAYy-IDqtAWxFdtPfyGmg0AbAiZV9RQ90g"

class PlanRequest(BaseModel):
    plan_name: str
    calorie_target: int
    protein_pct: int
    carbs_pct: int
    fat_pct: int

@app.post("/generate-meals")
async def generate_meals(plan: PlanRequest):
    client = genai.Client(api_key=GEMINI_API_KEY)
    protein_g = round((plan.calorie_target * plan.protein_pct / 100) / 4)
    carbs_g = round((plan.calorie_target * plan.carbs_pct / 100) / 4)
    fat_g = round((plan.calorie_target * plan.fat_pct / 100) / 9)

    prompt = f"""Tu es nutritionniste. Génère un plan repas pour une journée.
Plan: {plan.plan_name}, {plan.calorie_target} kcal, proteines {plan.protein_pct}% ({protein_g}g), glucides {plan.carbs_pct}% ({carbs_g}g), lipides {plan.fat_pct}% ({fat_g}g).
Reponds UNIQUEMENT en JSON sans backticks:
{{"repas":[{{"type":"Petit dejeuner","nom":"...","description":"...","calories":400,"proteines":20,"glucides":45,"lipides":12,"ingredients":["...","...","..."]}},{{"type":"Dejeuner","nom":"...","description":"...","calories":600,"proteines":35,"glucides":65,"lipides":18,"ingredients":["...","...","..."]}},{{"type":"Snack","nom":"...","description":"...","calories":200,"proteines":10,"glucides":25,"lipides":6,"ingredients":["...","..."]}},{{"type":"Diner","nom":"...","description":"...","calories":500,"proteines":30,"glucides":50,"lipides":15,"ingredients":["...","...","..."]}}]}}"""

    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    result = json.loads(text)
    return result

@app.get("/")
async def root():
    return {"status": "API is running"}
