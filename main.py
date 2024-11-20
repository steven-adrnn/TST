from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from supabase import create_client, Client
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import urllib.parse
import uvicorn

app = FastAPI()

# Konfigurasi Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Model User
class User(BaseModel):
    id: str
    email: str
    name: str = None

# Endpoint Login Google
@app.get("/auth/google")
async def google_login(request: Request):
    # Parameter OAuth Google yang lebih lengkap
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": "https://your-vercel-domain.vercel.app/auth/google/callback",  # Pastikan sesuai dengan yang di Google Console
        "response_type": "code",  # Tambahkan ini
        "scope": "openid email profile",
        "state": "random_state_value",  # Tambahkan state untuk keamanan
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
async def google_auth_callback(code: str):
    try:
        # Tukar authorization code dengan access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "https://your-vercel-domain.vercel.app/auth/google/callback"
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

# Endpoint yang memerlukan autentikasi
@app.get("/protected")
async def protected_route(token: str):
    try:
        # Verifikasi token Supabase
        user = supabase.auth.get_user(token)
        return {"message": f"Authenticated as {user.user.email}"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token"
        )
        
@app.get("/")
async def root():
    return {"message": "Hello from SmartGreen!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

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

# if __name__ == '__main__':
#     app.run()
