import os
import httpx
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional
from urllib.parse import urlencode

# Load environment variables
load_dotenv()

app = FastAPI()
security = HTTPBearer()

# Supabase client setup
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Configuration
FRONTEND_URL = "https://smartgreen-kappa.vercel.app"
BACKEND_URL = "https://smartgreen-kappa.vercel.app"  # Update if your backend URL is different
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def login(provider: str, request: Request):
    # Construct the OAuth URL with all necessary parameters
    params = {
        "provider": provider,
        "redirect_to": f"{BACKEND_URL}/auth/callback",
        "scopes": "email",  # Add any additional scopes you need
    }
    
    auth_url = f"{supabase_url}/auth/v1/authorize?{urlencode(params)}"
    return RedirectResponse(url=auth_url)

@app.get("/auth/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    # Handle OAuth error
    if error:
        return JSONResponse(
            status_code=400,
            content={
                "error": error,
                "error_description": error_description
            }
        )

    # Handle missing code
    if not code:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing authorization code"}
        )
    
    try:
        # Exchange token with Supabase
        async with httpx.AsyncClient() as client:
            token_params = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{BACKEND_URL}/auth/callback",
            }
            
            response = await client.post(
                f"{supabase_url}/auth/v1/token?grant_type=authorization_code",
                json=token_params,
                headers={
                    "apikey": supabase_key,
                    "Content-Type": "application/json"
                }
            )

            print(f"Supabase Response: {response.status_code}")  # Debug log
            print(f"Response Content: {response.text}")  # Debug log

        if response.status_code != 200:
            return JSONResponse(
                status_code=400,
                content={"error": f"Failed to exchange code for token: {response.text}"}
            )

        data = response.json()
        
        # Get user data from response
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        user = data.get("user", {})
        user_id = user.get("id")

        if not user_id or not access_token:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid token response"}
            )

        # Create our own JWT token
        jwt_token = create_access_token({"sub": user_id})
        
        # Redirect to frontend with all tokens
        params = {
            "access_token": jwt_token,
            "supabase_token": access_token,
            "refresh_token": refresh_token
        }
        
        redirect_url = f"{FRONTEND_URL}/callback.html#{urlencode(params)}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        print(f"Error in callback: {str(e)}")  # Debug log
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )

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