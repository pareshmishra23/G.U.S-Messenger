from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import socketio
import jwt
from passlib.context import CryptContext
import bcrypt
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Socket.IO setup
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Create the main app
app = FastAPI()

# Socket.IO app
socket_app = socketio.ASGIApp(sio, app)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_online: bool = False

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_online: bool

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    receiver_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: str = "text"

class MessageCreate(BaseModel):
    receiver_id: str
    content: str
    message_type: str = "text"

class MessageResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    timestamp: datetime
    message_type: str

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authentication Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create new user
    user_dict = user_data.dict()
    user_dict["password_hash"] = hash_password(user_data.password)
    del user_dict["password"]
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    
    return UserResponse(**user.dict())

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    # Find user
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    
    # Update user online status
    await db.users.update_one({"id": user["id"]}, {"$set": {"is_online": True}})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }

@api_router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # Update user online status
    await db.users.update_one({"id": current_user.id}, {"$set": {"is_online": False}})
    return {"message": "Logged out successfully"}

# User Routes
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_current_user)):
    users = await db.users.find({"id": {"$ne": current_user.id}}).to_list(1000)
    return [UserResponse(**user) for user in users]

@api_router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# Message Routes
@api_router.post("/messages", response_model=MessageResponse)
async def send_message(message_data: MessageCreate, current_user: User = Depends(get_current_user)):
    # Check if receiver exists
    receiver = await db.users.find_one({"id": message_data.receiver_id})
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    # Create message
    message_dict = message_data.dict()
    message_dict["sender_id"] = current_user.id
    message = Message(**message_dict)
    
    await db.messages.insert_one(message.dict())
    
    # Emit message to receiver via Socket.IO
    await sio.emit('new_message', {
        'message': message.dict(),
        'sender': UserResponse(**current_user.dict()).dict()
    }, room=f"user_{message_data.receiver_id}")
    
    return MessageResponse(**message.dict())

@api_router.get("/messages/{user_id}", response_model=List[MessageResponse])
async def get_messages(user_id: str, current_user: User = Depends(get_current_user)):
    messages = await db.messages.find({
        "$or": [
            {"sender_id": current_user.id, "receiver_id": user_id},
            {"sender_id": user_id, "receiver_id": current_user.id}
        ]
    }).sort("timestamp", 1).to_list(1000)
    
    return [MessageResponse(**message) for message in messages]

# Socket.IO Events
connected_users = {}

@sio.event
async def connect(sid, environ, auth):
    print(f"Client {sid} connected")
    
    # Extract token from auth
    if auth and 'token' in auth:
        try:
            payload = jwt.decode(auth['token'], JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                connected_users[sid] = user_id
                await sio.enter_room(sid, f"user_{user_id}")
                
                # Update user online status
                await db.users.update_one({"id": user_id}, {"$set": {"is_online": True}})
                
                # Notify other users
                await sio.emit('user_online', {'user_id': user_id}, skip_sid=sid)
                
        except jwt.PyJWTError:
            await sio.disconnect(sid)

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")
    
    if sid in connected_users:
        user_id = connected_users[sid]
        del connected_users[sid]
        
        # Update user offline status
        await db.users.update_one({"id": user_id}, {"$set": {"is_online": False}})
        
        # Notify other users
        await sio.emit('user_offline', {'user_id': user_id}, skip_sid=sid)

@sio.event
async def send_message(sid, data):
    if sid not in connected_users:
        return
    
    sender_id = connected_users[sid]
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not receiver_id or not content:
        return
    
    # Create message
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )
    
    await db.messages.insert_one(message.dict())
    
    # Get sender info
    sender = await db.users.find_one({"id": sender_id})
    
    # Emit to receiver
    await sio.emit('new_message', {
        'message': message.dict(),
        'sender': UserResponse(**sender).dict()
    }, room=f"user_{receiver_id}")

# WebRTC Signaling Events
@sio.event
async def call_user(sid, data):
    if sid not in connected_users:
        return
    
    caller_id = connected_users[sid]
    receiver_id = data.get('receiver_id')
    offer = data.get('offer')
    
    if not receiver_id or not offer:
        return
    
    # Get caller info
    caller = await db.users.find_one({"id": caller_id})
    
    # Emit call invitation to receiver
    await sio.emit('incoming_call', {
        'caller': UserResponse(**caller).dict(),
        'offer': offer
    }, room=f"user_{receiver_id}")

@sio.event
async def call_accepted(sid, data):
    if sid not in connected_users:
        return
    
    receiver_id = connected_users[sid]
    caller_id = data.get('caller_id')
    answer = data.get('answer')
    
    if not caller_id or not answer:
        return
    
    # Emit answer to caller
    await sio.emit('call_accepted', {
        'answer': answer
    }, room=f"user_{caller_id}")

@sio.event
async def call_rejected(sid, data):
    if sid not in connected_users:
        return
    
    receiver_id = connected_users[sid]
    caller_id = data.get('caller_id')
    
    if not caller_id:
        return
    
    # Emit rejection to caller
    await sio.emit('call_rejected', {}, room=f"user_{caller_id}")

@sio.event
async def end_call(sid, data):
    if sid not in connected_users:
        return
    
    user_id = connected_users[sid]
    other_user_id = data.get('other_user_id')
    
    if not other_user_id:
        return
    
    # Emit call ended to other user
    await sio.emit('call_ended', {}, room=f"user_{other_user_id}")

@sio.event
async def ice_candidate(sid, data):
    if sid not in connected_users:
        return
    
    user_id = connected_users[sid]
    other_user_id = data.get('other_user_id')
    candidate = data.get('candidate')
    
    if not other_user_id or not candidate:
        return
    
    # Forward ICE candidate to other user
    await sio.emit('ice_candidate', {
        'candidate': candidate
    }, room=f"user_{other_user_id}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Use the socket_app instead of app for ASGI
app = socket_app