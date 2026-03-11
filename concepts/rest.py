import uuid

from fastapi import Depends, FastAPI,APIRouter,status,HTTPException,UploadFile, File
from sqlalchemy import create_engine,Column,Integer,String,UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel
import os
import random

from concepts.kafka_producer import KafkaEventProducer

app=FastAPI()
app_v1=APIRouter(prefix="/api/v1",tags=["v1"])

producer = KafkaEventProducer()

engine = create_engine("postgresql://agriadmin:agriadmin123@localhost:5632/agri_db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    await producer.start()

users=["user1","user2","user3"]

class User(Base):
    __tablename__="users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)

class DiseasePrediction(Base):
    __tablename__ = "disease_prediction"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    image_path = Column(String, nullable=False)
    disease_type = Column(String, nullable=True)
    disease_level = Column(String, nullable=True)
    healthy = Column(String, nullable=False)

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str

diseases = [
    "Leaf Blight",
    "Powdery Mildew",
    "Rust",
    "Leaf Spot"
]

levels = [
    "Low",
    "Medium",
    "High"
]

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

@app_v1.post("/detect-disease", status_code=status.HTTP_200_OK)
async def detect_disease(file: UploadFile = File(...), db: Session = Depends(get_db)):

    # generate unique id
    pred_id = uuid.uuid4()

    # file path
    file_path = f"{UPLOAD_DIR}/{pred_id}_{file.filename}"

    # save image
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # mock prediction
    disease_detected = random.choice([True, False])

    if disease_detected:
        disease_type = random.choice(diseases)
        disease_level = random.choice(levels)
        healthy = "no"
    else:
        disease_type = "None"
        disease_level = "None"
        healthy = "yes"

    # store in database
    prediction = DiseasePrediction(
        id=pred_id,
        image_path=file_path,
        disease_type=disease_type,
        disease_level=disease_level,
        healthy=healthy
    )

    db.add(prediction)
    db.commit()

    # Send event to Kafka
    await producer.send_event(
    event_type="disease_detect",
    payload={
        "prediction_id": str(pred_id),
        "disease_detected": disease_detected,
        "disease_type": disease_type,
        "disease_level": disease_level,
        "image_path": file_path
    }
)

    return {
        "prediction_id": pred_id,
        "disease_detected": disease_detected,
        "disease_type": disease_type,
        "disease_level": disease_level,
        "image_path": file_path
    }

app.include_router(app_v1)
