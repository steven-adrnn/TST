import os
import httpx
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()
security = HTTPBearer()

# Supabase client setup
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@app.get("/auth/login/{provider}")
async def login(provider: str):
    url = f"{supabase_url}/auth/v1/authorize?provider={provider}&redirect_to=https://smartgreen-kappa.vercel.app/auth/callback"
    return RedirectResponse(url)

@app.get("/auth/callback", response_class=HTMLResponse)
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "Missing authorization code"}
    
    # Exchange token with Supabase
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{supabase_url}/auth/v1/token", json={
            "provider": "oauth",
            "code": code,
            "redirect_to": "https://smartgreen-kappa.vercel.app/auth/callback"
        })

    if response.status_code != 200:
        return {"error": "Failed to exchange code for token"}

    data = response.json()
    user_id = data.get("user", {}).get("id")
    
    if not user_id:
        return {"error": "User ID not found in token response"}

    # Create JWT token
    access_token = create_access_token({"sub": user_id})
    
    # Redirect to frontend with token
    response_redirect = RedirectResponse(url=f"/?token={access_token}")
    return response_redirect

@app.get("/")
async def root():
    return {"message": "Hello from SmartGreen!"}

@app.get('/api/users')
def get_users(current_user: str = Depends(get_current_user)):
    users = [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Jane Smith"},
    ]
    return users

@app.get('/api/tools')
def get_tools(current_user: str = Depends(get_current_user)):
    tools = [
        {"id": 1, "name": "Cangkul"},
        {"id": 2, "name": "Pupuk"},
        {"id": 3, "name": "Sprayer"},
    ]
    return tools

@app.post("/auth/logout")
async def logout():
    return RedirectResponse(url="/")