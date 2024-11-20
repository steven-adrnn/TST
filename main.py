from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
import httpx
import urllib.parse
import secrets

app = FastAPI()

# Tambahkan CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Konfigurasi Supabase dan OAuth
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Sesuaikan redirect URI untuk production
REDIRECT_URI = "https://smartgreen-kappa.vercel.app/auth/google/callback"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Endpoint Login Google
@app.get("/auth/google")
async def google_login():
    # Generate state untuk keamanan
    state = secrets.token_urlsafe(16)
    
    # Parameter OAuth Google
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline"
    }
    
    # Encode parameter dengan benar
    query_string = urllib.parse.urlencode(params)
    
    # Konstruksi URL dengan benar
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    # Redirect langsung ke URL Google
    return RedirectResponse(url=auth_url)

# Callback Handler Google OAuth
@app.get("/auth/google/callback")
async def google_auth_callback(code: str, state: str = None):
    try:
        # Tukar authorization code dengan access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            tokens = token_response.json()

        # Ambil informasi pengguna dari Google
        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            user_info = user_info_response.json()

        # Proses login/registrasi di Supabase
        email = user_info['email']
        name = user_info.get('name', '')

        # Cek apakah user sudah terdaftar di Supabase
        try:
            # Coba login dengan email
            auth_response = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "email": email
            })
        except Exception:
            # Jika belum terdaftar, lakukan sign up
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": os.urandom(16).hex(),  # Generate random password
                "options": {
                    "data": {
                        "name": name
                    }
                }
            })

        # Dapatkan token dari Supabase
        session = auth_response.session
        access_token = session.access_token

        return {
            "access_token": access_token,
            "user": {
                "email": email,
                "name": name
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )

# Endpoint lainnya tetap sama
@app.get("/")
async def root():
    return {"message": "Hello from SmartGreen!"}

@app.get('/api/users')
def get_users():
    users = [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Jane Smith"},
    ]
    return users

@app.get('/api/tools')
def get_tools():
    tools = [
        {"id": 1, "name": "Cangkul"},
        {"id": 2, "name": "Pupuk"},
        {"id": 3, "name": "Sprayer"},
    ]
    return tools