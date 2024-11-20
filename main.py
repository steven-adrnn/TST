from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from supabase import create_client, Client
import os
import uvicorn

# Inisialisasi Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI()

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = supabase.auth.sign_in(email=form_data.username, password=form_data.password)
    if user.error:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": user.user.id, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    user = supabase.auth.get_user(token)
    if user.error:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

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