from pydantic import BaseModel 

class UserParams(BaseModel):
    username: str
    email: str
    password: str

class LoanParams(BaseModel):
    amount: float
    term: int
    monthly_income: float

class PaymentParams(BaseModel):
    loan_id: int
    amount: float
