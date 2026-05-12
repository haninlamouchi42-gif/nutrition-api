from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = "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"

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
                    {
                        "role": "system",
                        "content": "Tu es un nutritionniste expert. Reponds UNIQUEMENT en JSON valide sans aucun texte avant ou apres."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=60.0
        )
        data = response.json()
        
        if "choices" not in data:
            return {"error": str(data)}
        
        text = data["choices"][0]["message"]["content"]
        result = json.loads(text)
        return result

@app.get("/")
async def root():
    return {"status": "API is running"}
