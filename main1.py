from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time
from models import Loan


DATABASE_URL = "mysql+mysqlconnector://root:@localhost/evelyn hone"

origins = ["http://localhost:3000", "http://127.0.0.1:5500"]

# Create the database engine
engine = create_engine(DATABASE_URL)

# Create the base class for the ORM models
Base = declarative_base()

# Define a User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String)

# Create the session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define FastAPI app
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods="*", allow_headers=["*"])

API_KEY = "47dfbed73u2n49nchd782"

@app.middleware("http")
async def check_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    print(api_key)

    # if api_key != API_KEY:
    #     return JSONResponse(status_code=403, content={"detail": "Invalid API Key..."})

    response = await call_next(request)
    return response


# Pydantic model for request body validation
class UserCreate(BaseModel):
    name: str
    email: str


def get_message():
    return "Hello from dependency"

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)

    process_time = time.time() - start_time
    print(f"Request: {request.method} {request.url} completed in {process_time:.2f} sec")

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nonsniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response

@app.get("/")
def home_root(message: str = Depends(get_message)):
    return {"message": message}


@app.post("/users/")
def create_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/")
def get_users(db: SessionLocal = Depends(get_db)):
    users = db.query(User).all()
    return users


@app.get("/search/{id}")
def search_users(id: int, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

@app.put("/update/{id}")
def update_details(incomingUser: UserCreate, id: int, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.name = incomingUser.name
    user.email = incomingUser.email
    db.commit()
    db.refresh(user)
    return user




