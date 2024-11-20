from fastapi import FastAPI, Depends, HTTPException, status
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

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

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
    # Supabase akan menangani redirect ke Google
    auth_url = supabase.auth.get_oauth_url('google')
    return {"auth_url": auth_url}

@app.post("/login")
async def login(token: str):
    """Verifikasi token dari Supabase"""
    try:
        # Verifikasi token dari Supabase
        user = supabase.auth.get_user(token)
        
        # Generate JWT untuk aplikasi Anda sendiri
        jwt_token = jwt.encode(
            {"sub": user.user.id}, 
            JWT_SECRET, 
            algorithm='HS256'
        )
        
        return {
            "access_token": jwt_token, 
            "token_type": "bearer",
            "user": user.user.user_metadata
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)