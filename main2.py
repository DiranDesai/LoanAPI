from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from models import User, Loan
from schemas import UserParams, LoanParams, PaymentParams
from database import get_db, SessionLocal
from utils import hashPassword, create_access_token, verify_password
from datetime import timedelta
import jwt


# Secret key for encoding & decoding JWT
SECRET_KEY = "$2b$12$rRUvZq2IlUMss/ypmcBwbujoUj6X29TbyfbU0XOJTvR"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


app = FastAPI()


# # Middleware for JWT authentication
# class JWTAuthMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         if request.url.path not in ["/login", "/docs", "/openapi.json", "/token"]:  # Skip login/docs
#             authorization: str = request.headers.get("Authorization")
#             if not authorization or not authorization.startswith("Bearer "):
#                 raise HTTPException(status_code=401, detail="Missing or invalid token")

#             token = authorization.split(" ")[1]
#             try:
#                 payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#                 username: str = payload.get("sub")
#                 print(username)
#                 # if username is None or username not in fake_users_db:
#                 #     raise HTTPException(status_code=401, detail="Invalid token")
#                 # request.state.user = fake_users_db[username]  # Attach user to request
#             except jwt.ExpiredSignatureError:
#                 raise HTTPException(status_code=401, detail="Token expired")
#             except jwt.PyJWTError:
#                 raise HTTPException(status_code=401, detail="Invalid token")

#         return await call_next(request)


#  Add middleware to FastAPI
# app.add_middleware(JWTAuthMiddleware)

@app.get("/")
def render_home():
    return {"Hello": "World"}

@app.post("/register")
def registerUser(user: UserParams, db: SessionLocal = Depends(get_db)):
    userExists = db.query(User).filter(User.email == user.email).first()
    print(userExists)
    if userExists:
        print(user)
        raise HTTPException(status_code=404, detail="User with that email already exists")
    
    hashedPassword = hashPassword(user.password)
    db_user = User(username=user.username, email=user.email, password=hashedPassword)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User registered successfully"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token({"id": user.id, "username": user.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/protected")
def protectedRoute(currentUser: dict = Depends(verify_token)):
    print(currentUser)



@app.post("/apply")
def applyLoan(loan: LoanParams, db: SessionLocal = Depends(get_db), currentUser: dict = Depends(verify_token)):
    if not currentUser:
        raise HTTPException(status_code=401, detail="Invalid token")

    if (loan.amount / loan.monthly_income) > 5 or not (6 <= loan.term <= 36):
        raise HTTPException(status_code=400, detail="Loan amount or term not allowed")
    try:
        loan = Loan(user_id=currentUser["id"], amount=loan.amount, term=loan.term, monthly_income=loan.monthly_income, balance=loan.amount)

        db.add(loan)
        db.commit()
        db.refresh(loan)
        return {"message": "Loan submitted successfully..."}

    except Exception as e:
        print(f"Error occured.. {e}")


    


@app.post("/repay-loan")
def repayLoan(request: PaymentParams, currentUser: dict = Depends(verify_token), db: SessionLocal = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == request.loan_id, Loan.user_id == currentUser["id"]).first()
    print(loan)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if not loan.status == "Approved":
        raise HTTPException(status_code=400, detail="Loan is not approved yet")

    if request.amount <= 0 or request.amount > loan.balance:
        raise HTTPException(status_code=400, detail="Invalid payment amount")

    loan.balance -= request.amount
    db.commit()
    return {"message": "Payment successful", "remaining_balance": loan.balance}


@app.get("/loans")
def getLoans():
    return {"message", "getting loans"}