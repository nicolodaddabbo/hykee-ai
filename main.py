from utils import data_management as dm, llm_inference
from fastapi import FastAPI
from models.fa_request import FARequest

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hykee AI API is running!"}

@app.post("/api/generate/financial-analysis")
async def generate_financial_analysis(data: FARequest):
    context = dm.get_context_from_request(data.model_dump(mode="json"))
    response = llm_inference.generate_financial_analysis(dm.balance_json_to_text(context))
    return {"message": "AI financial analysis generated successfully!", "data": response}

# if __name__ == "__main__":
llm_inference.load_model()
