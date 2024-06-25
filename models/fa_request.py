from pydantic import BaseModel
from typing import Optional
from models.balance import Balance
from models.company_score import CompanyScore

class FARequest(BaseModel):
    vatNumber: Optional[str] = None
    companyName: Optional[str] = None
    balance: Optional[Balance] = None
    score: Optional[CompanyScore] = None