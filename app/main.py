import os
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security.api_key import APIKeyHeader
from models.fa_request import FARequest
from utils import data_management as dm, llm_inference

app = FastAPI()

API_KEY = os.getenv("HYKEE_AI_API_KEY")
API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header == f"Bearer {API_KEY}":
        return api_key_header
    else:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )

@app.get("/")
async def root(api_key: str = Depends(get_api_key)):
    return {"message": "Hykee AI API is running!"}

@app.post("/api/generate/financial-analysis")
async def generate_financial_analysis(data: FARequest, api_key: str = Depends(get_api_key)):
    context = dm.get_context_from_request(data.model_dump(mode="json"))
    print(f"Request for generation with context: {context}")
    response = llm_inference.generate_financial_analysis(dm.balance_json_to_text(context))
    return {"message": "AI financial analysis generated successfully!", "data": response}

@app.get("/api/json-to-text/balance")
async def json_to_text_balance(data: FARequest, api_key: str = Depends(get_api_key)):
    return dm.balance_json_to_text(dm.get_context_from_request(data.model_dump(mode="json")))

# if __name__ == "__main__":
llm_inference.load_model()
