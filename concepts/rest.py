import uuid

from fastapi import Depends, FastAPI,APIRouter,status,HTTPException
from sqlalchemy import create_engine,Column,Integer,String,UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel

app=FastAPI()
app_v1=APIRouter(prefix="/api/v1",tags=["v1"])

engine = create_engine("postgresql://agriadmin:agriadmin123@db_service:5432/agri_db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

users=["user1","user2","user3"]

class User(Base):
    __tablename__="users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app_v1.get("/users/{id}", status_code=status.HTTP_200_OK)
def getuserbyid(id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    return {"user": user}

@app_v1.get("/users", status_code=status.HTTP_200_OK)
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users": users}

@app_v1.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(name=user.name, email=user.email, password=user.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response = UserResponse(id=new_user.id, name=new_user.name, email=new_user.email)
    return response

app.include_router(app_v1)
