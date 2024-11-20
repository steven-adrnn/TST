from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from jose import jwt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
JWT_SECRET = os.getenv('JWT_SECRET')
REDIRECT_URL = os.getenv('REDIRECT_URL', 'http://localhost:8000/callback')

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Verify JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('sub')
        
        # Fetch user from Supabase
        user = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user.data[0]
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/login/google")
async def login_google():
    """Redirect to Google OAuth via Supabase"""
    try:
        # Gunakan metode baru untuk sign_in_with_oauth
        auth_response = supabase.auth.sign_in_with_oauth({
            'provider': 'google',
            'options': {
                'redirect_to': REDIRECT_URL
            }
        })
        
        return {
            "auth_url": str(auth_response.url),
            "status": "Silakan redirect ke URL ini"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/callback")
async def oauth_callback(request: Request):
    """Callback untuk OAuth"""
    try:
        # Ambil parameter dari query
        code = request.query_params.get('code')
        error = request.query_params.get('error')

        if error:
            return {"status": "error", "message": error}

        if not code:
            raise HTTPException(status_code=400, detail="Kode otorisasi tidak ditemukan")

        # Proses pertukaran kode
        response = supabase.auth.exchange_code_for_session(code)
        
        return {
            "status": "success", 
            "session": response.session.access_token if response.session else None,
            "user": response.user.user_metadata if response.user else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(token: str):
    """Verifikasi token dari Supabase"""
    try:
        # Verifikasi token dari Supabase
        response = supabase.auth.get_user(token)
        user = response.user
        
        # Generate JWT untuk aplikasi Anda sendiri
        jwt_token = jwt.encode(
            {"sub": user.id}, 
            JWT_SECRET, 
            algorithm='HS256'
        )
        
        return {
            "access_token": jwt_token, 
            "token_type": "bearer",
            "user": user.user_metadata
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Hello from SmartGreen!"}

@app.get('/api/users')
async def get_users(current_user: dict = Depends(get_current_user)):
    users = [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Jane Smith"},
    ]
    return users

@app.get('/api/tools')
async def get_tools(current_user: dict = Depends(get_current_user)):
    tools = [
        {"id": 1, "name": "Cangkul"},
        {"id": 2, "name": "Pupuk"},
        {"id": 3, "name": "Sprayer"},
    ]
    return tools

# Vercel API Route Handler
def handler(event, context):
    import serverless_wsgi
    return serverless_wsgi.handle_request(app, event, context)