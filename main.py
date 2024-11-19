import uvicorn
# from fastapi import FastAPI
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from jose import jwt
import os
from fastapi.middleware.cors import CORSMiddleware
import traceback
import logging

# Inisialisasi Supabase
url: str = os.getenv('SUPABASE_URL')
key: str = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log environment variables untuk debugging
logger.info(f"Supabase URL: {url}")
logger.info(f"Supabase Key: {'*' * len(key) if key else 'Not Set'}")

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
    try:
        # Proses callback dari provider
        response = supabase.auth.sign_in_with_oauth({
            'provider': 'google',
            'code': code
        })
        
        # Tangani response dengan lebih baik
        if response.user:
            return {
                "user": response.user.dict(),
                "session": response.session.dict() if response.session else None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autentikasi gagal"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

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
    try:
        return {"message": "Hello from SmartGreen!"}
    except Exception as e:
        print(f"Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))



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
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)