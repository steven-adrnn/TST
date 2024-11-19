import uvicorn
# from fastapi import FastAPI
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from jose import jwt
import os
from fastapi.middleware.cors import CORSMiddleware

# Inisialisasi Supabase
url: str = os.getenv('SUPABASE_URL')
key: str = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)

app = FastAPI()

# Konfigurasi OAuth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Fungsi Verifikasi Token
async def verify_token(token: str):
    try:
        # Dekode token Supabase
        payload = jwt.decode(
            token, 
            os.getenv('JWT_SECRET'), 
            algorithms=["HS256"]
        )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint Login OAuth
@app.post("/login")
async def login(provider: str = "google"):
    # Redirect ke halaman OAuth Supabase
    auth_url = supabase.auth.get_oauth_url(provider)
    return {"auth_url": auth_url}

# Endpoint Callback OAuth
@app.get("/auth/callback")
async def auth_callback(code: str):
    # Proses callback dari provider
    user = supabase.auth.sign_in_with_oauth({
        'provider': 'google',
        'code': code
    })
    return {"user": user}

# Endpoint Terproteksi
@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    # Verifikasi token sebelum akses
    user = await verify_token(token)
    return {"message": "Akses diberikan", "user": user}

@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        # Proses logout di Supabase
        supabase.auth.sign_out(token)
        return {"message": "Logout berhasil"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal logout"
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

if __name__ == '__main__':
    app.run()