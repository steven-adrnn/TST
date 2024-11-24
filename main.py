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

@app.get("/auth/login/google")
async def login_google():
    try:
        query_params = {
            "provider": "google",
            "redirect_to": f"{FRONTEND_URL}/auth/callback"
        }
        
        auth_url = f"{supabase_url}/auth/v1/authorize?{urlencode(query_params)}"
        print(f"Redirecting to: {auth_url}")  # Debug log
        return RedirectResponse(url=auth_url)
    except Exception as e:
        print(f"Error in login: {str(e)}")  # Debug log
        return JSONResponse(
            status_code=500,
            content={"error": f"Login error: {str(e)}"}
        )

@app.get("/auth/callback")
async def callback(request: Request):
    try:
        # Get all query parameters
        params = dict(request.query_params)
        print(f"Callback params: {params}")  # Debug log

        # Check for error in the callback
        if "error" in params:
            return JSONResponse(
                status_code=400,
                content={
                    "error": params.get("error"),
                    "error_description": params.get("error_description")
                }
            )

        # Get the code from query parameters
        code = params.get("code")
        if not code:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing authorization code"}
            )

        # Exchange the code for a token using Supabase client
        try:
            # Get session data from Supabase
            data = supabase.auth.exchange_code_for_session({
                "auth_code": code
            })
            
            print(f"Supabase auth response: {data}")  # Debug log

            # Extract user information
            session = data.session
            user = session.user
            
            if not user or not user.id:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Failed to get user information"}
                )

            # Create our JWT token
            access_token = create_access_token({"sub": user.id})
            
            # Redirect to frontend with token
            params = {
                "access_token": access_token,
                "refresh_token": session.refresh_token,
                "provider": "google"
            }
            
            redirect_url = f"{FRONTEND_URL}/callback.html#{urlencode(params)}"
            print(f"Redirecting to: {redirect_url}")  # Debug log
            return RedirectResponse(url=redirect_url)

        except Exception as e:
            print(f"Error exchanging code: {str(e)}")  # Debug log
            return JSONResponse(
                status_code=400,
                content={"error": f"Failed to exchange code: {str(e)}"}
            )

    except Exception as e:
        print(f"Callback error: {str(e)}")  # Debug log
        return JSONResponse(
            status_code=500,
            content={"error": f"Callback error: {str(e)}"}
        )

@app.get("/")
async def root():
    return {"message": "Hello from SmartGreen!"}

# ... rest of your endpoints remain the same ...

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