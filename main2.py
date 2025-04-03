from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, MessageType
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from models import User, Loan, Payment
from schemas import UserParams, LoanParams, PaymentParams
from database import get_db, SessionLocal
from utils import hashPassword, create_access_token, verify_password
from datetime import timedelta
from config import conf
from fastapi_utils.tasks import repeat_every
import jwt
import typing_inspect


# Secret key for encoding & decoding JWT
SECRET_KEY = "$2b$12$rRUvZq2IlUMss/ypmcBwbujoUj6X29TbyfbU0XOJTvR"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 8230

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


app = FastAPI()


# @app.on_event("startup")
# @repeat_every(seconds=10)  # Run this task every 10 seconds
# def print_message():
#     print("This message prints every 10 seconds!")

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

async def send_email(background_tasks: BackgroundTasks, subject: str, recipient: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

@app.post("/send-notification/")
async def notify_user(background_tasks: BackgroundTasks, email: str, loan_status: str):
    subject = f"Loan Status Update: {loan_status}"
    body = f"Your loan status has changed to: {loan_status}. Please check your dashboard for details."
    await send_email(background_tasks, subject, email, body)
    return {"message": "Notification sent"}

@app.post("/apply")
async def applyLoan(loan: LoanParams, background_tasks: BackgroundTasks, db: SessionLocal = Depends(get_db), currentUser: dict = Depends(verify_token)):
    user = db.query(User).filter(User.id == currentUser["id"]).first()
    if not currentUser:
        raise HTTPException(status_code=401, detail="Invalid token")

    if (loan.amount / loan.monthly_income) > 5 or not (6 <= loan.term <= 36):
        raise HTTPException(status_code=400, detail="Loan amount or term not allowed")
    try:
        loan = Loan(user_id=currentUser["id"], amount=loan.amount, term=loan.term, monthly_income=loan.monthly_income, balance=loan.amount)

        db.add(loan)
        db.commit()
        db.refresh(loan)

        #application_date = datetime.utcnow()

        subject = f"Thank you for applying for a loan with LoanBase."
        body = f"Dear {user.username},\n\n" \
                f"Thank you for applying for a loan with LoanBase. We have received your application and our team is currently reviewing your request.\n\n" \
                f"**Application Details:**\n" \
                f"- **Loan Amount:** ${loan.amount}\n" \
                f"- **Loan Type:** {"Personal loan"}\n" \
                f"- **Application Date:** {1}\n\n" \
                f"We will update you within {1} business days.\n\n" \
                f"Best regards,\n"
        await send_email(background_tasks, subject, "kunjesai55@gmail.com", body)

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

    payment = Payment(user_id=currentUser["id"], loan_id=request.loan_id, amount=request.amount)
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {"message": "Payment successful", "remaining_balance": loan.balance}


@app.get("/loans")
def getLoans(currentUser: dict = Depends(verify_token), db: SessionLocal = Depends(get_db)):
    loans = db.query(Loan).all()
    return {"loans": loans}