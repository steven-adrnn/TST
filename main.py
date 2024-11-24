import os
import httpx  # Pastikan Anda menginstal httpx
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sessions import SessionMiddleware, get_session
from fastapi_sessions.frontends.implementations.itsdangerous import ItsDangerousBackend
from fastapi_sessions.session import Session
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Supabase client setup
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session setup
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
backend = ItsDangerousBackend(secret=SECRET_KEY, lifetime_seconds=3600)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Dependency to get current user from session
async def get_current_user(session: Session = Depends(get_session)):
    if "user_id" not in session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session["user_id"]

@app.get("/auth/login/{provider}")
async def login(provider: str):
    url = f"{supabase_url}/auth/v1/authorize?provider={provider}&redirect_to=https://smartgreen-kappa.vercel.app/auth/callback"
    return RedirectResponse(url)

@app.get("/auth/callback", response_class=HTMLResponse)
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "Missing authorization code"}
    
    # Melakukan pertukaran token dengan Supabase
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{supabase_url}/auth/v1/token", json={
            "provider": "oauth",
            "code": code,
            "redirect_to": "https://smartgreen-kappa.vercel.app/auth/callback"
        })

    # Cek apakah permintaan berhasil
    if response.status_code != 200:
        return {"error": "Failed to exchange code for token"}

    data = response.json()

    # Ambil user_id dari data yang diterima
    user_id = data.get("user", {}).get("id")
    if not user_id:
        return {"error": "User  ID not found in token response"}

    # Simpan user_id dalam session
    session = request.session
    session["user_id"] = user_id

    response_redirect = RedirectResponse(url="/")
    return response_redirect

@app.get("/")
async def root():
    return {"message": "Hello from SmartGreen!"}

@app.get('/api/users', dependencies=[Depends(get_current_user)])
def get_users():
    users = [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Jane Smith"},
    ]
    return users

@app.get('/api/tools', dependencies=[Depends(get_current_user)])
def get_tools():
    tools = [
        {"id": 1, "name": "Cangkul"},
        {"id": 2, "name": "Pupuk"},
        {"id": 3, "name": "Sprayer"},
    ]
    return tools

@app.post("/auth/logout")
async def logout(session: Session = Depends(get_session)):
    session.clear()  # Clear the session
    return RedirectResponse(url="/")

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)