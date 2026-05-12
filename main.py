from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = "AIzaSyAYy-IDqtAWxFdtPfyGmg0AbAiZV9RQ90g"
genai.configure(api_key=GEMINI_API_KEY)

class PlanRequest(BaseModel):
    plan_name: str
    calorie_target: int
    protein_pct: int
    carbs_pct: int
    fat_pct: int

@app.post("/generate-meals")
async def generate_meals(plan: PlanRequest):
    protein_g = round((plan.calorie_target * plan.protein_pct / 100) / 4)
    carbs_g = round((plan.calorie_target * plan.carbs_pct / 100) / 4)
    fat_g = round((plan.calorie_target * plan.fat_pct / 100) / 9)

    prompt = f"""Tu es un nutritionniste expert. Génère un plan repas complet pour une journée.
Plan: {plan.plan_name}
Objectif: {plan.calorie_target} kcal
Proteines: {plan.protein_pct}% ({protein_g}g)
Glucides: {plan.carbs_pct}% ({carbs_g}g)
Lipides: {plan.fat_pct}% ({fat_g}g)

Reponds UNIQUEMENT en JSON valide sans texte avant ou apres et sans backticks:
{{"repas": [{{"type": "Petit dejeuner","nom": "nom du repas","description": "description courte","calories": 400,"proteines": 20,"glucides": 45,"lipides": 12,"ingredients": ["ingredient1","ingredient2","ingredient3"]}},{{"type": "Dejeuner","nom": "nom du repas","description": "description courte","calories": 600,"proteines": 35,"glucides": 65,"lipides": 18,"ingredients": ["ingredient1","ingredient2","ingredient3"]}},{{"type": "Snack","nom": "nom du repas","description": "description courte","calories": 200,"proteines": 10,"glucides": 25,"lipides": 6,"ingredients": ["ingredient1","ingredient2"]}},{{"type": "Diner","nom": "nom du repas","description": "description courte","calories": 500,"proteines": 30,"glucides": 50,"lipides": 15,"ingredients": ["ingredient1","ingredient2","ingredient3"]}}]}}"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    result = json.loads(text)
    return result

@app.get("/")
async def root():
    return {"status": "API is running"}
